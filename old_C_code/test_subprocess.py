import subprocess
import time

def main():
    # Start the C++ program as a subprocess
    process = subprocess.Popen(
        ["sudo", "./counting-code","5", "6", "13", "19", "21", "26", "-f", "'example'", "-c"],  # Path to your compiled C++ program
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    try:
        while True:
            # Send a request to the C++ program
            process.stdin.write("GET\n")
            process.stdin.flush()

            # Read the response
            response = process.stdout.readline().strip()
            if response:
                print(f"Received number: {response}")

            # Wait before sending the next request
            time.sleep(0.5)  # Request data every 1 second

    except KeyboardInterrupt:
        print("Terminating...")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()
