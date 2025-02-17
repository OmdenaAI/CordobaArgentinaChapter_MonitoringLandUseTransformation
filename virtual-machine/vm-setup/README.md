# Virtual Machine Setup

## Requirements

* `Oracle VM VirtualBox Manager`, version 7.0 was used for this example. You can check downloads for your OS [`here`](https://www.virtualbox.org/wiki/Downloads).
* 10Gb+ of free disk space on the local machine you'll be using.
* If you are going to build the machine from scratch, refer to the [`Operative System Download`](#ubuntu) section

<a name="ova"></a>
## How to mount a Virtual Machine in .ova format

1) Once VirtualBox is installed in your system, download and decompress the .rar file sent over Slack. You can find it pinned to the backend-and-api channel, together with a credentials file. The password in there needs to be used for the .rar. 
2) Start VirtualBox, go to `File` → `Import Appliance`.<br><br><p align='center'><img src="src/appliance-import-1.jpg" alt='Ubuntu-EC2-Sim.ova'></p>
3) Select the `Ubuntu-EC2-Sim.ova`from the location you saved it to, and click `Next`. <br><br><p align='center'><img src="src/appliance-import-2.jpg" alt='Ubuntu-EC2-Sim.ova'></p>
4) I recommend you change the Machine Base Folder to one you can relate to the project <br><br><p align='center'><img src="src/appliance-import-3.jpg" alt='Appliance Settings 1'></p>
5) Same for the base folder where the machine is actually going to be saved once built, recommended you create/pic a directory you can easily relate to the project. <br><br><p align='center'><img src="src/appliance-import-4.jpg" alt='Appliance Settings 2'></p>
6) The rest of the settings should work nicely as a starting point. Press `Finish`and continue to VirtualBox main menu.
7) You should see the machine added now. Go to start, and this first time, pick the `Normal Start`<br><br><p align='center'><img src="src/appliance-import-5.jpg" alt='VirtualBox Main Menu'></p>
8) As the Machine was powered off, this first normal start will take a while and will show the startup operations in the terminal, so you'll have to wait.<br><br><p align='center'><img src="src/appliance-import-6.jpg" alt='VirtualBoxBox Window 1'></p>
9) Once all is loaded and ready, you'll be prompted credentials, look for those at the Slack Channel, too.<br><br><p align='center'><img src="src/appliance-import-7.jpg" alt='VirtualBox Window 2'></p>
10) Now the terminal is ready for you to work on the machine! <br><br><p align='center'><img src="src/appliance-import-8.jpg" alt='VirtualBox Window 3'></p>
11) In my case, I prefer to use an SSH client of my choice called [`Bitvise SSH Client`](https://bitvise.com/download-area), you can download that one too. I find it useful as it comes with a copy paste config I find comfortable, and also has SFTP integrated, which you'll need to transfer files into the machine (not the only method, but by far the most comfortable one).
12) If you choose to use an SSH client, then make sure after this startup you `Stop` the virtual machine with the `Save State` option.<br><br><p align='center'><img src="src/appliance-import-9.jpg" alt='Save Machine'></p><br><br>That will let you pick headless start the next time, and use you client of choice comfortably.<br><br><p align='center'><img src="src/appliance-import-10.jpg" alt='Headless Start'></p>

### Running the services.

* In order to be exported, the VM had to be powered off, which means the services are not running. To get those running again, you need to use the compose file:

```bash
flo@ec2-sim:~/argentina-land-use/redis$ sudo docker-compose up --build -d
```

* Notice the docker-compose commands need to run from the directory the file is at, if you are not providing a reference to the durectory.

* If you want or need to stop the services (E.G. because you need to rebuild)

```bash
flo@ec2-sim:~/argentina-land-use$ sudo docker-compose stop
```

Again, from the directory where the `docker-compose.yaml` file is.


* To check the running containers
```bash
flo@ec2-sim:~/argentina-land-use$ sudo docker ps
```

### Modifying the services.

You can use the machine as a development enviroment, of course. If you want to test new code, granted no new installs are needed, you can replace the code with new ones, stop the services and re-start/re-deploy as show in the previous step. To transfer files into the VM, you'll need an FTP client, such as [`File-Zilla`](https://filezilla-project.org/download.php?type=client) or [`WinSCP`](https://winscp.net/eng/download.php). Notice that [`Bitvise SSH Client`](https://bitvise.com/download-area) has a built in SFTP client that you can use too.


## How to setup a virtual machine from scratch using VirtualBox
<a name="ubuntu"></a>
1) After VirtualBox is set, we'll need to pick an operative system for the machine. In the setup chosen for the project, Ubuntu server 24.04.1 LTS was used, you can download the image from [this location](https://ubuntu.com/download/server).
2) With the ISO file ready, we'll start the process to set the new machine<br><br><p align='center'><img src="src/new-virtual-machine-1.jpg" alt='VirtualBox - New virtual Machine'></p><br><br>Beware that the new machine setter could start in Expert Mode, and you might want to change to guided mode.<br><br><p align='center'><img src="src/new-virtual-machine-2.jpg" alt='New Virtual Machine'></p><br><br>
3) Give the machine a name of your choice.<br><br><p align='center'><img src="src/new-virtual-machine-3-7.jpg" alt='New Virtual Machine'></p><br><br>
4) Create a directory where the machine files will be stored. This does not need the same directory where the image is, just a directory that will make it easy for you to find the project files.
5) Provide the path to the ISO file downloaded with Ubuntu Server.
6) Leave this option `unticked`, because if the Operative System allows it, it'll launch the operative system installation unattended. Notice that slaunch does not mean it will completely run unattended, but that you do not need to worry to start the machine for the first time and get it running. The System type will be recognized from the ISO file (that's why it's greyed out).
7) Move to next screen.
8) Setup your credentials on the left<br><br><p align='center'><img src="src/new-virtual-machine-8-9.jpg" alt='New Virtual Machine'></p><br><br>
9) Move to next screen.
10) To simulate similar conditions to the chose EC2 instance, we'll use 1024Mb RAM<br><br><p align='center'><img src="src/new-virtual-machine-10-12.jpg" alt='New Virtual Machine'></p><br><br>
11) In a similar fashion, we'll set CPUs to 1 or 2 to mimic lighter EC2 instances.
12) Move to Next.
13) We'll create a hard drive using VirtualBox, assigning 10GB (again, similar to EC2)<br><br><p align='center'><img src="src/new-virtual-machine-13-15.jpg" alt='New Virtual Machine'></p><br><br>
14) Be sure to tick this option, because if you do not, you'll need to manually allocate the disk space on the command line once you are in Ubuntu.
15) Next.
16) Check everything mactches what you need, you can go back and modify, or press finish.<br><br><p align='center'><img src="src/new-virtual-machine-16.jpg" alt='New Virtual Machine'></p><br><br>
17) The Operative System installation will start, you'll be ocassionally promoted to pick options. Remember that best strategy is to simply work with your keyboard, using a mouse on such interface, even when there's an option to enable it, might be tricky, I do not recommend.<br><br><p align='center'><img src="src/new-virtual-machine-17.jpg" alt='New Virtual Machine'></p><br><br>
18) To ensure your input devices work as intended, I recommend using the Identify Keyboard option. You'll be promted to press certain keys and answer what keys are or not present in your physical keyboard.<br><br><p align='center'><img src="src/new-virtual-machine-18.jpg" alt='New Virtual Machine'></p><br><br>
19) You'll continue to get prompted options... be patient. Once the full process is over, you'll be prompted to login<br><br><p align='center'><img src="src/appliance-import-7.jpg" alt='Login'></p>
20) Once you are logged in and the installation process is over, I recommend you go back to the main VirtualBox window, pick `Stop` → `Save State`.<br><br><p align='center'><img src="src/new-virtual-machine-20.jpg" alt='New Virtual Machine'></p><br><br>This will allow you login next time using an SSH client, which I recommend. To know more about this option, refer to [`this section above`](#ova).
