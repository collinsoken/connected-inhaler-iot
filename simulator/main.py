"""
Entry point: runs the sensor simulator for all configured patients concurrently.
Run with: python -m simulator.main
Stop with Ctrl+C (triggers a graceful shutdown across all patient threads).
"""

import threading

from simulator.config import PATIENTS
from simulator.patient_worker import run_patient


def main():
    stop_event = threading.Event()
    threads = []

    for patient in PATIENTS:
        t = threading.Thread(target=run_patient, args=(patient, stop_event), daemon=True)
        t.start()
        threads.append(t)

    print(f"Simulator running for {len(PATIENTS)} patients. Press Ctrl+C to stop.")

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        stop_event.set()
        for t in threads:
            t.join(timeout=5)
        print("All patient threads stopped.")


if __name__ == "__main__":
    main()
