# jeyspecialneedscentre-backend

<p align="center">
    <img src="assets/Logo.png" alt="Logo" border="0">
    <br>Backend server for <a href="https://jeyspecialneedscentre.com/">Jey special needs centre</a>, built on Django
</p>

---

<p align="center">
    <a href="https://github.com/SVijayB/jeyspecialneedscentre-backend/pulls">
        <img src="https://img.shields.io/github/issues-pr/SVijayB/jeyspecialneedscentre-backend.svg?style=for-the-badge&amp;logo=opencollective" alt="GitHub pull-requests">
    </a>
<a href="https://github.com/SVijayB/jeyspecialneedscentre-backend/issues">
    <img src="https://img.shields.io/github/issues/SVijayB/jeyspecialneedscentre-backend.svg?style=for-the-badge&amp;logo=testcafe" alt="GitHub issues">
    </a>
<a href="https://github.com/SVijayB/jeyspecialneedscentre-backend/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/SVijayB/jeyspecialneedscentre-backend.svg?style=for-the-badge&amp;logo=bandsintown" alt="GitHub contributors">
    </a>
<a href="https://github.com/SVijayB/jeyspecialneedscentre-backend/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/SVijayB/jeyspecialneedscentre-backend?style=for-the-badge&amp;logo=appveyor" alt="GitHub license">
    </a>
<a href="https://github.com/SVijayB/jeyspecialneedscentre-backend">
    <img src="https://img.shields.io/github/repo-size/SVijayB/jeyspecialneedscentre-backend?style=for-the-badge&amp;logo=git" alt="GitHub repo size">
    </a>
<a href="https://github.com/SVijayB/jeyspecialneedscentre-backend/blob/master/.github/CODE_OF_CONDUCT.md">
    <img src="https://img.shields.io/badge/code%20of-conduct-ff69b4.svg?style=for-the-badge&amp;logo=crowdsource" alt="Code of Conduct">
    </a>
<a href="https://github.com/SVijayB/jeyspecialneedscentre-backend/blob/master/.github/CONTRIBUTING.md">
    <img src="https://img.shields.io/static/v1?style=for-the-badge&amp;logo=opensourceinitiative&amp;label=Open&amp;message=Source%20%E2%9D%A4%EF%B8%8F&amp;color=blueviolet" alt="Open Source Love svg1">
    </a>
</p>

## Table of Contents

-   [Motivation](#Motivation)
-   [Installation](#Installation)
-   [Usage](#Usage)
    -   [Project Demo](#Demo)
-   [Contributing](#Contributing)
-   [License](#License)

## Motivation

<!--- Insert product screenshot below --->

<!-- ![Product Screenshot](https://media.giphy.com/media/L1R1tvI9svkIWwpVYr/giphy.gif) -->

Jey Special Needs Centre provides ABA services for children with Autism, ADHD, Down syndrome, Cerebral palsy, Learning Disability, based on the science of Applied Behavior Analysis (ABA). Their mission is to empower children with special needs to reach their full potential and lead fulfilling lives.

This repository contains the backend code for their management system, built using Django. It handles user authentication, data management, and serves as the backbone for the web application.


## Installation

### Prerequisites
- Python 3.11+ 
- MongoDB Atlas account (free tier available)
- Git

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/SVijayB/jeyspecialneedscentre-backend
cd jeyspecialneedscentre-backend
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv

source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your MongoDB Atlas URI and other settings
# See .env.example for all required variables
```

5. **Run migrations (if any)**
```bash
cd src
python manage.py migrate
```

6. **Start the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Contributing

To contribute to this repository, fork it, create a new branch and send us a pull request. Make sure you read [CONTRIBUTING.md](https://github.com/SVijayB/jeyspecialneedscentre-backend/blob/master/.github/CONTRIBUTING.md) before sending us Pull requests.

Thanks for contributing to Open-source! ❤️

## License

This repository is under The GPL-3.0 License. Read the [LICENSE](https://github.com/SVijayB/jeyspecialneedscentre-backend/blob/master/LICENSE) file for more information.

---

<img src="assets/footercredits.png" width = "600px">
