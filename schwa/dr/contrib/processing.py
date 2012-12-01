# vim: set ts=2 et:
import argparse
import io
import sys
import threading
try:
  import zmq
except ImportError:
  zmq = None

from ..reader import Reader
from ..writer import Writer


def stream_coroutine(istream, ostream, doc_class=None, automagic=False):
  reader = Reader(istream, doc_class, automagic)
  writer = Writer(ostream, reader.doc_schema)
  for doc in reader:
    res = yield(doc)
    writer.write(res or doc)


def zmq_coroutine(context, dealer_url, doc_class=None, automagic=False):
  istream = io.BytesIO()
  ostream = io.BytesIO()
  reader = Reader(istream, doc_class, automagic)
  writer = Writer(ostream, reader.doc_schema)
  socket = context.socket(zmq.REP)
  socket.connect(dealer_url)
  while True:
    msg = socket.recv()
    istream.write(msg)
    istream.seek(0)
    for doc in reader:
      res = yield(doc)
      writer.write(res or doc)
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
  if any(getattr(args, a, None) for a in ('serve_url', 'worker_url')):
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
  else:
    process(stream_coroutine(sys.stdin, sys.stdout, doc_class))
