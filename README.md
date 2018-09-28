# ICRH Conditioning Python tools
 
## Preamble
In order to be able to retrieve the data from the dfci acquisition computer, one should first setup ssh to authenticate via public/private keypairs instead of password. 

* Step 1: use ssh-keygen on your local system to generate public and private keys. In a local terminal, type:

```
$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/Home/JH218595/.ssh/id_rsa): 
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /Home/JH218595/.ssh/id_rsa.  
Your public key has been saved in /Home/JH218595/.ssh/id_rsa.pub. <--------- this file is important below
The key fingerprint is:
c9:d7:c6:ad:6e:23:0a:cd:1e:66:77:8e:b2:66:f2:2e JH218595@nunki.intra.cea.fr
```

* Step 2: use ssh_copy-id to add on the remote computer (dfci) your public rsa key to the file authorized_keys located in ~/.ssh/. 

Example:
```
cd ~/.ssh/
ssh-copy-id -i id_rsa.pub dfci@dfci
```

NB : the home (~) directory should be set to 755 permission (or 700??), otherwise SSH will keep asking for a password (cf. https://unix.stackexchange.com/questions/292168/scp-command-keeps-asking-password) 


* Step 3: Test if the SSH copy works without requiring password on your local computer: 

Example:

```
scp dfci@dfci:/media/ssd/Conditionnement/2017-02-27_14-42-12.csv .
dfci@dfci's password: [JH218595@nunki data ]> scp dfci@dfci:/media/ssd/Conditionnement/2017-02-27_14-42-12.csv .
2017-02-27_14-42-12.csv  
```

