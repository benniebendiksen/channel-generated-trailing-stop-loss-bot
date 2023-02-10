# AWS Instructions
This document is intended to guide you through the steps of setting up your own free-tier Amazon aws EC2 Linux-based Virtual Machine instance and, 
additionally, configuring its linux system to run the trend activated bot. 

Binance boasts the highest trade volume of any crypto exchange, as well as the largest listings of coins with the most competitive trade fees available. For the best performances with lowest latency, we will want to interact with Binance via an Amazon AWS virtual machine in the ap-northeast-1a region.

## Starting an AWS Free-Tier EC2 Instance
Amazon AWS allows for a free 12 month use virtual machine instance for new AWS customers. Their Linux and Windows t2.micro instances includes 750 hours
of free uses each month for one year with up 30 GB of free storage space.

### Sign up with AWS
Sign up for free, as a new user, with Amazon aws:  
[https://aws.amazon.com/account/sign-up](https://aws.amazon.com/account/sign-up)

![Instance Home](instance_home)

### Creating Your First Free Tier EC2 Instance
Once signed in, from the aws Console, click on "EC2".
Under 'Resources' click on "Instances", and then click "Launch instances".
Under 'Application and OS Images (Amazon Machine Image)' the 'Quick Start' tab should already be highlighted for you along with the Amazon Linux option underneath it.
Most of the default settings shown at this point will work fine. The free tier t2.micro instance is already set as the default under 'Instance type'.

To use an SSH client (e.g., .pem file) to connect to your Linux instance perform the following:
- Under 'Key pair (login)' click "Create new key pair".
- Type in a Key pair name such as "MY_AWS_KEYS" and see that the "RSA" and ".pem" buttons are checked. Click on "Create key pair"
- Store the .pem file that gets downloaded in a folder of your choosing.
- From within that folder make your keys read-writable only by you by running 
  ```
  chmod 600 MY_AWS_KEYS.pem
  ```
  from a command line.
- The only setting you need change is, under 'Network settings' click "Edit" and, under the 'Subnet' drop-down menu, select the option that states 
“Availability Zone: ap-northeast-1a”. Region ap-northeast corresponds to Tokyo, and sub-region 1a indicates the area within ap-northeast wherein the Binance server is located.
The more we reduce latency between ourselves and the exchange, the better.
- You are allowed up to 30 giB of free storage so under 'Configure storage' you might as well click "Add new volume" and replace the 8 value with, say, 20.
- You can finally create "Launch Instance" on the bottom right of the screen!

### Running and Connecting to your EC2 Instance
When back on the Console you'll see that your new instance has "Running" under the 'instance state' field. Click on the 'Instance ID' value of this same row.
- If for some reason your instance did not reveal "Running" under the 'Instance state' field, simply click the 'Instance state' drop down and select "Start instance".
- Now click on "Connect", ensure you are under the 'SSH client' section, and copy the ssh command seen on the bottom under 'Example'. An example copied ssh command is the following:
  ```
  ssh -i "MY_AWS_KEYS.pem" ec2-user@ec2-13-113-62-229.ap-northeast-1.compute.amazonaws.com
  ```

On your local machine, open a commmand line interface under the folder in which you saved the .pem file; paste your copied ssh command there and run it.
You should now have command line access to your 12 month free aws EC2 virtual machine instance!


![Amazon Instance](amazon_instance)


## Configuring your AWS Instance
We will need to prepare your EC2 instance to be able to run our python program with all of its dependencies. We start by installing Python 3.10 into our instance.

### Installing Python 3.10 into your Instance
Follow this straightforward guide from 'Getting Started' up to, and including 'Step 3':
[https://techviewleo.com/how-to-install-python-on-amazon-linux-2/](https://techviewleo.com/how-to-install-python-on-amazon-linux-2/)

### Enable sqlite on your Python 3.10 install
Down the line, we will want to gather data regarding the outcome of our buy and sell activity (i.e., was it a profitable trade or not). We therefore will want to store data into a database file and query it. Though sqlite comes as a feature to Python 3.10, in our case we have to install it explicitly since we did our own Python 3.10 build.
Run:
```
sudo yum install sqlite-devel
```

From the Python3.10 root directory, run the following to recompile and rebuild Python:
```
./configure --enable-loadable-sqlite-extensions && make && sudo make install
```

### Install Anaconda on your EC2 Instance
To make for the easiest reproduction of the trend activated bot environment in our EC2 instance, let's quickly install Anaconda.

Copy link address from Anaconda installer archive; in EC2 instance terminal, type:
```
wget https://repo.continuum.io/archive/Anaconda2-4.1.1-Linux-x86_64.sh
```

followed by:
```
bash what_Anaconda_you_downloaded_Linux_x86_64.sh
```

followed by:
```
source .bashrc
```

Now you should be able to use Anaconda and all its feautures within your EC2 instance.
## Running Trend Activated Bot from your EC2 Instance
You are almost ready to run trend activated bot from your virtual machine. Let us copy the project over into the VM.

### Copy Project into your EC2 Instance
From the folder on your local machine that holds your .pem file, scp the project into the VM following the format:
```
scp -i "MY_AWS_KEYS" -r </path/to/project/trend-activated-trailing-stop-loss-bot ec2-user@ec2-13-113-62-229.ap-northeast-1.compute.amazonaws.com:/home/ec2-user/>
```
Note that the ec2 instance name comes from the previously mentioned ssh command.

### Permanently Set Keys as Environment Variables and Run Bot
To permanently set your keys as os environment variables, from the EC2 instance terminal type:
```
echo "export API_KEY=aaa">>~/.bash_profile
echo "export API_SECRET=bbb">>~/.bash_profile
```
using your specific key values

Don't forget to create a conda environment from the project's provided yml file; from the project root directory, run:
```
conda env create -f trend_activated_bot_env.yml
```

You can now finally run your program! Just type:
```
python3.10 main.py
```
and watch the program execute :)



