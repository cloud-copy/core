import multiprocessing as mp
mp.set_start_method('fork')

JOIN_TIMEOUT = 1

if __name__ == '__main__':
    main()


def main():
    # server entrypoint: fork and monitor the API server and task worker
    server = mp.Process(target=start_server)
    worker = mp.Process(target=start_worker)
    processes = [('server', server), ('worker', worker)]
    server.start()
    worker.start()

    while True:
        new = []
        # continuously join and restart the processes
        for i, (name, process) in enumerate(processes):
            process.join(JOIN_TIMEOUT)
            if process.is_alive():
                continue

            # restart the process if it died
            if name == 'server':
                process = Process(target=start_server)
            else:
                process = Process(target=start_worker)
            process.start()
            new.append((name, process))
        processes = new


def start_server():
    # start uvicorn server
    import uvicorn
    from cloudcopy.server.config import settings
    uvicorn.run('cloudcopy.server.api:server', port=settings.API_PORT)


def start_worker():
    # start huey worker (consumer)
    from .tasks import worker
    consumer = worker.create_consumer()
    consumer.run()
