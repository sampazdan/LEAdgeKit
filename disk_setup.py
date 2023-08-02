import os
import subprocess
import psutil
import sys

disk = ""
device = ""
mount_point = ""
#FDISK_INPUT is input string for FDISK, it 
FDISK_INPUT = "g\nn\n\n\n\nw\n"

def locate_disk():
    print("\nBrookgreen Technologies 2023")
    print("Revision A disk setup")
    print("----------------------------")
    print("\nLocating disk targets...")
    lsblk = subprocess.Popen(('lsblk', '-o', 'name'), stdout = subprocess.PIPE)
    disk = subprocess.check_output(('grep', 'nvme'), stdin = lsblk.stdout, text = True)
    disk = disk.split("\n")[0]
    device = "/dev/" + disk

    if input(f"\nFound NVMe disk '{disk}'. Press enter to continue setup or enter 'q' to quit.\n This will erase all drive data.") in ('q', 'Q'):
        exit(0)

    print("Unmounting, preparing for formatting")
    try:
        subprocess.run(("sudo", "umount", "-l", device), check=True)
        
    except:
        print("Main disk already unmounted...")
    print("Unmounting partitions...")

    try:
        unmount_all_partitions(disk)
    except:
        print("Error unmounting partitions")

    print("Partitions unmounted... Removing partitions...")

    try:
        subprocess.run(("sudo", "parted", "-s", device, "mklabel", "gpt"), check = True)
    except:
        print("Error rewriting partition table. Exiting...")

    print("New partition table created, creating new formatted partition...")

    try:
        subprocess.run(("sudo", "fdisk", device), input = FDISK_INPUT, text = True, check = True)
        subprocess.run(("sudo", "mkfs.ext4", device + "p1"), check = True)
    except:
        print("Error creating and formatting partition... Exiting.")

    print("Making new mount directory and mounting disk...")

    try:
        os.makedirs(mount_point, exist_ok = True)
    except:
        print("Invalid mount point. Please rerun with valid mount point. Exiting...")
        exit(1)

    try:
        subprocess.run(("sudo", "mount", device + "p1", mount_point), check = True)
    except:
        print("Error mounting, either remount manually or rerun program. Exiting...")
        exit(1)

    print(f"\n\033[1;32;40mSuccess! Disk {disk} is now formatted and mounted at {mount_point})\033[0m\n")
    

def unmount_all_partitions(device):

    for part in psutil.disk_partitions():
        if device in part.device:
            print(f"Unmounting {part.device} mounted on {part.mountpoint}")
            try:
                subprocess.run(('sudo', 'umount', '-l', part.device), check=True)
            except:
                print(f"Error unmounting {part.device}. Exiting...")
                exit(1)
   

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No mount point given, defaulting to /mnt/nvme")
        mount_point = "/mnt/nvme"
    else:
        mount_point = sys.argv[1]

    locate_disk()
