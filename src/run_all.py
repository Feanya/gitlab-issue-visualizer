import time

import download
import render
from src import time_string

if __name__ == "__main__":
    print("Start download and parsing")
    download_start = time.time()
    download.main()
    download_finished = time.time()
    print("Start plotting")
    render_start = time.time()
    render.main()
    render_finished = time.time()
    print("Finished")

    download_time_taken = download_finished - download_start
    render_time_taken = render_finished - render_start
    total_time_taken = render_finished - download_start
    print(f"download.py took {time_string(download_time_taken)}")
    print(f"render.py took {time_string(render_time_taken)}")
    print(f"Total time {time_string(total_time_taken)}")
