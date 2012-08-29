import sys
import threading
import argparse
try:
  import zmq
except ImportError:
  zmq = None
from StringIO import StringIO
from .reader import Reader
from .writer import Writer

def stream_coroutine(istream, ostream, doc_class=None):
  writer = Writer(ostream)
  for doc in Reader(doc_class).stream(istream):
    res = yield(doc)
    writer.write_doc(res or doc)

def zmq_coroutine(context, dealer_url, doc_class=None):
  istream = StringIO()
  ostream = StringIO()
  reader = Reader(doc_class)
  writer = Writer(ostream)
  socket = context.socket(zmq.REP)
  socket.connect(dealer_url)
  while True:
    msg = socket.recv()
    istream.write(msg)
    istream.seek(0)
    for doc in reader.stream(istream):
      res = yield(doc)
      writer.write_doc(res or doc)
    ostream.seek(0)
    socket.send(ostream.getvalue())
    istream.truncate(0)
    ostream.truncate(0)

arg_parser = argparse.ArgumentParser(add_help=False)
if zmq:
  _megroup = arg_parser.add_mutually_exclusive_group()
  _megroup.add_argument('--serve', dest='serve_url', metavar="ADDRESS", default=None, help='Serve from the specified address, e.g. tcp://*:7300')
  _megroup.add_argument('--worker', dest='worker_url', metavar="ADDRESS", default=None, help='Acquire work from the specified address')
  arg_parser.add_argument('--nthreads', default=1, type=int, help='In --serve or --worker mode, how many worker threads to provide (default: %(default)s)')

def run_processor(process, args, doc_class=None, dealer_url='inproc://workers'):
  if not (args.serve_url or args.wroker_url):
    process(stream_coroutine(sys.stdin, sys.stdout, doc_class))
  else:
    context = zmq.Context(1)
    if args.serve_url:
      clients = context.socket(zmq.ROUTER)
      clients.bind(args.serve_url)
      workers = context.socket(zmq.DEALER)
      workers.bind(dealer_url)
    else:
      dealer_url = args.worker_url

    run = lambda: process(zmq_coroutine(context, dealer_url, doc_class))
    threads = [threading.Thread(target=run) for i in xrange(args.nthreads)]
    for thread in threads:
      thread.start()

    if args.serve_url:
      zmq.device(zmq.QUEUE, clients, workers)

