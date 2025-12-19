@dataclass
class Eleventye9a16667(JavaScriptProfile):
    owner: str = "11ty"
    repo: str = "eleventy"
    commit: str = "e9a16667cbf44226d4dc88ac18241003e05908d2"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

CMD ["npm", "test"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Workbox1893b3f6(JavaScriptProfile):
    owner: str = "GoogleChrome"
    repo: str = "workbox"
    commit: str = "1893b3f6ca3d82338f18acc84309f2f38fc67292"
    test_cmd: str = "npm run test_node -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

# Install system dependencies required for building some native modules and git for cloning
RUN apt-get update && apt-get install -y git python3 make g++ && rm -rf /var/lib/apt/lists/*


# Shallow clone the repository
RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

# Install dependencies and build the project (required for tests to find built modules)
RUN npm ci && npm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Habiticae0af620b(JavaScriptProfile):
    owner: str = "HabitRPG"
    repo: str = "habitica"
    commit: str = "e0af620b4045d46dffb4c22ea01f95ba8a8af009"
    test_cmd: str = "npm run test:api:unit -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:20

RUN apt-get update && apt-get install -y git python3 build-essential && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

# The postinstall script in package.json handles:
# 1. gulp build
# 2. cd website/client && npm install
# We need to ensure dependencies for the main app are installed first.
# Also, Habitica expects a config.json file.
RUN cp config.json.example config.json
RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Modernizr1d4c9cee(JavaScriptProfile):
    owner: str = "Modernizr"
    repo: str = "Modernizr"
    commit: str = "1d4c9cee1f358f50c31be9a1f247e1153ed9143c"
    test_cmd: str = "npm test -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

# Install system dependencies including git and chromium for puppeteer/mocha-headless-chrome
RUN apt-get update && apt-get install -y \
    git \
    wget \
    gnupg \
    ca-certificates \
    chromium \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*


# Clone the repository
RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

# Install dependencies, skipping puppeteer browser download since we use system chromium
ENV PUPPETEER_SKIP_DOWNLOAD=true
ENV CHROME_PATH=/usr/bin/chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
RUN npm install

# Set CMD
CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Falcor39d64776(JavaScriptProfile):
    owner: str = "Netflix"
    repo: str = "falcor"
    commit: str = "39d64776cf9d87781b2791615dcbae73b2bcd2e1"
    test_cmd: str = "npm run test:only -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install --legacy-peer-deps

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Pm2ff1ca974(JavaScriptProfile):
    owner: str = "Unitech"
    repo: str = "pm2"
    commit: str = "ff1ca974afada8730aa55f8ed1df40e700cedbcb"
    test_cmd: str = "npm run test:unit"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git procps bc python3 && rm -rf /var/lib/apt/lists/*


RUN git clone https://github.com/{self.owner}/{self.repo}.git /testbed && \
WORKDIR /testbed
    npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Audiobookshelf626596b1(JavaScriptProfile):
    owner: str = "advplyr"
    repo: str = "audiobookshelf"
    commit: str = "626596b192013ba9f5a011dd110e288124c95ebe"
    test_cmd: str = "npm test -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-bullseye-slim

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    make \
    g++ \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


RUN git clone https://github.com/{self.owner}/{self.repo}.git /testbed && \
WORKDIR /testbed
    git checkout 626596b192013ba9f5a011dd110e288124c95ebe

# Install root dependencies
RUN npm ci

# Install client dependencies and build client
RUN cd client && npm ci && npm run generate

# Ensure we are back in root
WORKDIR /testbed

CMD ["npm", "start"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Sailsffebacc5(JavaScriptProfile):
    owner: str = "balderdashy"
    repo: str = "sails"
    commit: str = "ffebacc58c27f878c9373702bc3a3f91a02bca0c"
    test_cmd: str = "npm run custom-tests -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install
CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Vuebootstrapvue9a246f45(JavaScriptProfile):
    owner: str = "bootstrap"
    repo: str = "vue-bootstrap-vue"
    commit: str = "9a246f45fc813f161df291fc7d6197febf8afaf4"
    test_cmd: str = "yarn jest --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-bullseye-slim

RUN apt-get update && apt-get install -y git python3 make g++ && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN yarn install --frozen-lockfile

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Nodepostgresecff60dc(JavaScriptProfile):
    owner: str = "brianc"
    repo: str = "node-postgres"
    commit: str = "ecff60dc8aa0bd1ad5ea8f4623af0756a86dc110"
    test_cmd: str = "service postgresql start && sleep 5 && sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" && export PGPASSWORD=postgres && export PGUSER=postgres && export PGHOST=localhost && yarn test"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y \
    git \
    make \
    python3 \
    g++ \
    build-essential \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN yarn install
RUN yarn build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Claudecodetemplates734b8a50(JavaScriptProfile):
    owner: str = "davila7"
    repo: str = "claude-code-templates"
    commit: str = "734b8a50cc2cf55222643e32a3b205483e244747"
    test_cmd: str = "cd api && npm test -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install && \
    cd cli-tool && npm install && \
    cd ../api && npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Jsemotionb882bcba(JavaScriptProfile):
    owner: str = "emotion"
    repo: str = "js-emotion"
    commit: str = "b882bcba85132554992e4bd49e94c95939bbf810"
    test_cmd: str = "yarn jest --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git python3 build-essential && rm -rf /var/lib/apt/lists/*

RUN corepack enable


RUN git clone --depth 1 https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN yarn install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Enzyme61e1b47c(JavaScriptProfile):
    owner: str = "enzymejs"
    repo: str = "enzyme"
    commit: str = "61e1b47c4bdc4509b2ac286c0d3ae3df172d26f0"
    test_cmd: str = "npm run react 16 && npm run test:only -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Recoilc1b97f3a(JavaScriptProfile):
    owner: str = "facebookexperimental"
    repo: str = "Recoil"
    commit: str = "c1b97f3a0117cad76cbc6ab3cb06d89a9ce717af"
    test_cmd: str = "yarn relay"

    @property
    def dockerfile(self):
        return f"""FROM node:18

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN yarn install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Fastify970c5758(JavaScriptProfile):
    owner: str = "fastify"
    repo: str = "fastify"
    commit: str = "970c575832521fff01cc018d928d84454811173b"
    test_cmd: str = "npm run unit"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Superagentcec26064(JavaScriptProfile):
    owner: str = "forwardemail"
    repo: str = "superagent"
    commit: str = "cec260643d6d8854865cf6a18997606be4b150f6"
    test_cmd: str = "./node_modules/.bin/mocha --require should --trace-warnings --throw-deprecation --reporter spec --slow 2000 --timeout 5000 --exit test/*.js test/node/*.js"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git build-essential python3 && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

RUN npm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Supertest14d905dc(JavaScriptProfile):
    owner: str = "forwardemail"
    repo: str = "supertest"
    commit: str = "14d905dc313b7c050596342f833a52f0bc573c70"
    test_cmd: str = "npm test -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install
CMD ["npm", "test"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Revealjsbecc9bd1(JavaScriptProfile):
    owner: str = "hakimel"
    repo: str = "reveal.js"
    commit: str = "becc9bd19e418b75027b541c41952105a1425c96"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

# Install system dependencies for git and Puppeteer
RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*


# Clone the repository
RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

# Install dependencies
RUN npm install

# Build the project (some tests might depend on built assets)
RUN npm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Handsontablee71f0f42(JavaScriptProfile):
    owner: str = "handsontable"
    repo: str = "handsontable"
    commit: str = "e71f0f427c43eaaac9362d947270b8856a9766cd"
    test_cmd: str = "pnpm test"

    @property
    def dockerfile(self):
        return f"""FROM node:22-slim

RUN apt-get update && apt-get install -y git python3 make g++ && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm@10.12.2


RUN git clone https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN pnpm install && pnpm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Joi481e270e(JavaScriptProfile):
    owner: str = "hapijs"
    repo: str = "joi"
    commit: str = "481e270e6c4ff8728d6fda248fd83f6ff70f7ed9"
    test_cmd: str = "npx lab -t 100 -a @hapi/code -L -Y -v"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Impressjsc9f6c674(JavaScriptProfile):
    owner: str = "impress"
    repo: str = "impress.js"
    commit: str = "c9f6c67457ceee5a011e554f67c447113640777d"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:18

RUN apt-get update && apt-get install -y \
    git \
    wget \
    gnupg \
    ca-certificates \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    xfonts-75dpi \
    xfonts-base \
    fonts-liberation \
    libappindicator3-1 \
    lsb-release \
    xdg-utils \
    libx11-xcb1 \
    libxcb-dri3-0 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

RUN npm run build

COPY karma.conf.js /testbed/karma.conf.js

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jasmine(log)




@dataclass
class Htmlwebpackplugin9a39db80(JavaScriptProfile):
    owner: str = "jantimon"
    repo: str = "html-webpack-plugin"
    commit: str = "9a39db807c09d8e6145e5047cfe2ec5e928e1dee"
    test_cmd: str = "npm run test:only -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone https://github.com/{self.owner}/{self.repo}.git /testbed && \
WORKDIR /testbed
    git checkout 9a39db807c09d8e6145e5047cfe2ec5e928e1dee

RUN npm install --legacy-peer-deps

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Backbonee8bc45ac(JavaScriptProfile):
    owner: str = "jashkenas"
    repo: str = "backbone"
    commit: str = "e8bc45acb0a8b035fe5a0d7338e1b2757681564f"
    test_cmd: str = "npx karma start --browsers ChromeHeadlessNoSandbox --single-run"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git chromium && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install && npm install karma-chrome-launcher --save-dev

# Add ChromeHeadlessNoSandbox launcher to karma.conf.js
RUN sed -i "s/customLaunchers: {{/customLaunchers: {{\\n        ChromeHeadlessNoSandbox: {{\\n            base: 'ChromeHeadless',\\n            flags: ['--no-sandbox']\\n        }},/" karma.conf.js

# Build debug-info.js which is required by tests
RUN npm run build-debug

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jasmine(log)




@dataclass
class Hyperapp5a113fa0(JavaScriptProfile):
    owner: str = "jorgebucaran"
    repo: str = "hyperapp"
    commit: str = "5a113fa00450302be9234e0a74ee634ed5574243"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install
CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Jsoneditor0319b213(JavaScriptProfile):
    owner: str = "josdejong"
    repo: str = "jsoneditor"
    commit: str = "0319b2131df47f1220d74e3ff174d5c02973ec7d"
    test_cmd: str = "npm test -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Uptimekuma5d955f95(JavaScriptProfile):
    owner: str = "louislam"
    repo: str = "uptime-kuma"
    commit: str = "5d955f954b60410cd2dc5370d429753de524a2ef"
    test_cmd: str = "npm run test-backend"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    build-essential \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*


# Clone the repository
RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

# Install dependencies
RUN npm install

# Build the frontend
RUN npm run build

# Default command
CMD ["npm", "start"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Jsmarko24b9402c(JavaScriptProfile):
    owner: str = "marko"
    repo: str = "js-marko"
    commit: str = "24b9402cd54c3a74f200da0f79dd19350995a9ba"
    test_cmd: str = "env MARKO_DEBUG=1 ./node_modules/.bin/mocha --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git python3 build-essential && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install && npm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Jsmdx00046053(JavaScriptProfile):
    owner: str = "mdx"
    repo: str = "js-mdx"
    commit: str = "000460532e6a558693cbe73c2ffdb8d6c098a07b"
    test_cmd: str = "npm run test-api --workspaces --if-present"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

RUN npm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class PapaParseb10b87ef(JavaScriptProfile):
    owner: str = "mholt"
    repo: str = "PapaParse"
    commit: str = "b10b87ef8686c6f88299b50dd25e83606e9c36d4"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y \
    git \
    chromium \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install
RUN sed -i "s/'-f'/'-a', '[\"--no-sandbox\"]', '-f'/" tests/test.js

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Materialui1a233f88(JavaScriptProfile):
    owner: str = "mui"
    repo: str = "material-ui"
    commit: str = "1a233f8805ea20f456afd41165b1d6d9e22c0adb"
    test_cmd: str = "pnpm test:node run"

    @property
    def dockerfile(self):
        return f"""FROM node:22-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm@10.25.0


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN pnpm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_vitest(log)




@dataclass
class Nightwatch54c8550c(JavaScriptProfile):
    owner: str = "nightwatchjs"
    repo: str = "nightwatch"
    commit: str = "54c8550c75a16c61827c0bad043c7ffa073a52e6"
    test_cmd: str = "npm test -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install --ignore-scripts

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Nocke7418da2(JavaScriptProfile):
    owner: str = "nock"
    repo: str = "nock"
    commit: str = "e7418da29feb4a7bf0aa1612bfb9d32a4051651e"
    test_cmd: str = "npm test -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:20

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class NoVNCd44f7e04(JavaScriptProfile):
    owner: str = "novnc"
    repo: str = "noVNC"
    commit: str = "d44f7e04fc456844836c7c5ac911d0f4e8dd06e6"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    chromium \
    ca-certificates \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create a wrapper for chromium to always include --no-sandbox
RUN mv /usr/bin/chromium /usr/bin/chromium-orig && \
    echo '#!/bin/bash\n/usr/bin/chromium-orig --no-sandbox "$@"' > /usr/bin/chromium && \
    chmod +x /usr/bin/chromium

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV TEST_BROWSER_NAME=ChromeHeadless


# Clone the repository
RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

# Install dependencies
RUN npm install

# Command to keep container running
CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class JsPDFe6cf03db(JavaScriptProfile):
    owner: str = "parallax"
    repo: str = "jsPDF"
    commit: str = "e6cf03db2499ef0a9ccc54b2aba45156c5b32b3c"
    test_cmd: str = "npm run test-node"

    @property
    def dockerfile(self):
        return f"""FROM node:18

RUN apt-get update && apt-get install -y \
    git \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libv4l-0 \
    libxkbcommon0 \
    libasound2 \
    wget \
    gnupg \
    --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/google-chrome-stable


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

# Inject custom launcher into karma.conf.js
RUN sed -i "s/browsers: \['Chrome'\]/browsers: ['ChromeHeadlessNoSandbox']/" test/unit/karma.conf.js && \
    sed -i "/reporters: \[/i \ \ \ \ customLaunchers: {{\\n      ChromeHeadlessNoSandbox: {{\\n        base: 'ChromeHeadless',\\n        flags: ['--no-sandbox', '--disable-setuid-sandbox']\\n      }}\\n    }}," test/unit/karma.conf.js

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Filepond38294959(JavaScriptProfile):
    owner: str = "pqina"
    repo: str = "filepond"
    commit: str = "38294959147229eb09126008fc09d295da4e30cd"
    test_cmd: str = "npm test -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Reacttransitiongroup2989b5b8(JavaScriptProfile):
    owner: str = "reactjs"
    repo: str = "react-transition-group"
    commit: str = "2989b5b87b4b4d1001f21c8efa503049ffb4fe8d"
    test_cmd: str = "npm run testonly"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install --legacy-peer-deps

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Reactmarkdownfda7fa56(JavaScriptProfile):
    owner: str = "remarkjs"
    repo: str = "react-markdown"
    commit: str = "fda7fa560bec901a6103e195f9b1979dab543b17"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Nodemondaad5c16(JavaScriptProfile):
    owner: str = "remy"
    repo: str = "nodemon"
    commit: str = "daad5c162919fa6abff53be16832bdf55f2204ad"
    test_cmd: str = "for FILE in test/**/*.test.js; do echo $FILE; TEST=1 ./node_modules/.bin/mocha --exit --timeout 30000 $FILE || true; sleep 1; done"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install
CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Evergreen9b774aee(JavaScriptProfile):
    owner: str = "segmentio"
    repo: str = "evergreen"
    commit: str = "9b774aee2d794f6cf2f73a054bd33066ca5898a9"
    test_cmd: str = "yarn jest --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN yarn install --frozen-lockfile

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Serverlessde62c71e(JavaScriptProfile):
    owner: str = "serverless"
    repo: str = "serverless"
    commit: str = "de62c71e30855eff688f032ff10b9ad22de13afc"
    test_cmd: str = "npm test -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/{self.owner}/{self.repo}.git /testbed && git checkout de62c71e30855eff688f032ff10b9ad22de13afc
WORKDIR /testbed
RUN npm install
CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Jssqljs52e5649f(JavaScriptProfile):
    owner: str = "sql"
    repo: str = "js-sql.js"
    commit: str = "52e5649f3a3a2a46aa4ad58a79d118c22f56cf30"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM emscripten/emsdk:latest

RUN apt-get update && apt-get install -y git make python3 unzip curl libdigest-sha3-perl && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install
RUN npm run build

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Jsonserverf5dfdaff(JavaScriptProfile):
    owner: str = "typicode"
    repo: str = "json-server"
    commit: str = "f5dfdaff725ecd5384b1f922b37757f023e13b63"
    test_cmd: str = "npm test"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed
RUN npm install
CMD ["npm", "start"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)




@dataclass
class Webpack24e3c2d2(JavaScriptProfile):
    owner: str = "webpack"
    repo: str = "webpack"
    commit: str = "24e3c2d2c9f8c6d60810302b2ea70ed86e2863dc"
    test_cmd: str = "yarn test:base --verbose --testMatch '<rootDir>/test/*.basictest.js'"

    @property
    def dockerfile(self):
        return f"""FROM node:20-slim

RUN apt-get update && apt-get install -y git python3 build-essential && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN yarn install && yarn setup

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




@dataclass
class Ws726c3732(JavaScriptProfile):
    owner: str = "websockets"
    repo: str = "ws"
    commit: str = "726c3732b3e5319219ed73cac4826fd36917e2e1"
    test_cmd: str = "npm test -- --reporter spec"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


RUN git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/{self.owner}/{self.repo}.git /testbed
WORKDIR /testbed

RUN npm install

CMD ["/bin/bash"]"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)




