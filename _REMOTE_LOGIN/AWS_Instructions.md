# Purpose of Document
This document is intended to guide you through the steps of setting up your own free-tier Amazon aws EC2 Linux-based Virtual Machine instance and, 
additionally, configuring your linux system to run the trend activated bot.

## Starting an AWS Free-Tier EC2 Instance
Amazon AWS allows for a free 12 month use virtual machine instance for new AWS customers. Their Linux and Windows t2.micro instances includes 750 hours
of free uses each month for one year with up 30 GB of free storage space.

### Sign up with AWS
Sign up for free, as a new user, with Amazon aws:  
[https://aws.amazon.com/account/sign-up](https://aws.amazon.com/account/sign-up)

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
- Now click on "Connect", ensure you are under the 'SSH client' section, and copy the ssh command seen on the bottom under 'Example'.

On your local machine, open a commmand line interface under the folder in which you saved the .pem file; paste your copied ssh command there and run it.
You should now have command line access to your 12 month free aws EC2 virtual machine instance!
