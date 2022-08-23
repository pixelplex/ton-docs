# Using tonstarter-contracts

:::caution draft   
This is a concept article. We're still looking for someone experienced to write it.
:::

## Overview

A _tonstarter-contracts_ based on TypeScript and [mocha](https://mochajs.org/) unit tests framework. Tests are running inside Node.js by running TVM in web-assembly using _ton-contract-executor_.

* [GitHub repository](https://github.com/ton-defi-org/tonstarter-contracts)
* [Online IDE using Glitch](https://github.com/ton-defi-org/tonstarter-contracts)

```bash
git clone https://github.com/ton-defi-org/tonstarter-contracts
cd tonstarter-contracts
```

## TON Contract Executor

This library allows you to run Ton Virtual Machine locally and execute contract. That allows you to write & debug & fully test your contracts before launching them to the network.

TON Contract executor allows you to:

* execute smart contracts from FunC source code
* execute smart contracts from existing data & code Cells
* get TVM executing logs
* debug your contracts via debug primitives
* it handles internal state changes of contract data
* allows calling of so-called GET methods of smart contracts
* allows sending & debugging internal messages
* allows sending & debugging external messages
* allows debugging of messages sent by smart contract
* handle changes in smart contract code
* allows manipulations with C7 register of smart contract (including time, random seed, network config, etc.)
* allows you to make some gas optimizations

:::info
Basically you can **develop**, **debug**, and **fully cover your contract with unit-tests** fully locally without deploying it to the network.
:::

#### Links

* [GitHub repository](https://github.com/Naltox/ton-contract-executor)
* [npm.js](https://www.npmjs.com/package/ton-contract-executor)

## Example

:::tip
You can see example even without installation — using [Online IDE](https://glitch.com/edit/#!/remix/clone-from-repo?&REPO_URL=https%3A%2F%2Fgithub.com%2Fton-defi-org%2Ftonstarter-contracts.git).
:::

Feel free to check repository code to find how _counter smart contract_ testing works:
* [main.fc](https://github.com/ton-defi-org/tonstarter-contracts/blob/main/contracts/main.fc) — original smart contract code example.
* [counter.spec.ts](https://github.com/ton-defi-org/tonstarter-contracts/blob/main/test/counter.spec.ts) — test that cover counter methods.

### Step by step

To start and experiment just copy repository from GitHub:
```bash
git clone https://github.com/ton-defi-org/tonstarter-contracts
cd tonstarter-contracts
```

After that to see how tests work just write in tonstarter-contracts dir:

```bash
npm tun tests
```

You'll see in console result of basic tests checks.