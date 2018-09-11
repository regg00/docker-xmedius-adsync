# Docker Xmedius ADSync

A Dockerized version of the Active Directory sync tool from Xmedius which can be found here : https://support.xmedius.com/hc/en-us/articles/203824796-Active-Directory-Synchronization-Tool#topic_8A9ADCE658304BC7804528757C33CF65

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development or production purposes.

### Prerequisites

The only requirement here is Docker (obviously). Refer to the Docker official documentation on how to install it : https://docs.docker.com/install/#reporting-security-issues

### Installing and configuring

Here's what you need to do to get started :

#### Clone this repository somewhere 

```
git clone https://github.com/regg00/docker-xmedius-adsync ~/docker-xmedius-adsync
```

#### Edit the configuration (*default.yaml*) file located in **app/config/**. 

```
Refer to the official Xmedius documentation for instructions on how to complete the configuration file properly : https://support.xmedius.com/hc/en-us/articles/203824596

Basically you'll need :
* Portal URL
* Access token
* IP or hostname of you AD server
* Username and password of an authorized AD account
* DNS path of your environment
```

Build the image

```
1. cd ~/docker-xmedius-adsync
2. docker build -t docker-xmedius-adsync .
```

Create and run the container

```
docker run docker-xmedius-adsync
```

**That's it!!** The first sync will take some times depending of the size of your environment.
You can monitor the synchronisation process with : 
```
docker logs -f docker-xmedius-adsync
```


## Deployment

I simply added this line in my crontab to run a sync daily at midnight 

```
0 0 * * * docker start xmedius-ad-sync >/dev/null 2>&1
```

## Built With

* [Docker](https://docs.docker.com/)
* [Python](https://docs.python.org/3/)
* [Xmedius ADSync](https://support.xmedius.com/hc/en-us/articles/203824596)


## Authors

* **regg00@gmail.com** - *Initial work* - [regg00](https://github.com/regg00)

## Acknowledgments

* I used ubuntu:latest as a base image for the container. It can probably be changed to python:2.7. 

## Donation
If that helped you, let me know by email. You can also support me with this link : https://paypal.me/regg00

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details