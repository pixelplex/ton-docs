---
description: In this tutorial, you will learn how to fully work with wallets, messages and smart contracts.
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Overview

## 👋 Introduction

Learning how wallets and transactions work on TON before beginning smart contracts development is essential. This knowledge will help developers understand the interaction between wallets, messages, and smart contracts to implement specific development tasks.

In this section we’ll learn to create operations without using pre-configured functions to understand development workflows. All references necessary for the analysis of this tutorial are located in the references chapter.

## 💡 Prerequisites

This tutorial requires basic knowledge of Javascript and Typescript or Golang. It is also necessary to hold at least 3 TON (which can be stored in an exchange account, a non-custodial wallet, or by using the telegram bot wallet). It is necessary to have a basic understanding of [cell](/learn/overviews/cells), [addresses in TON](/learn/overviews/addresses), [blockchain of blockchains](/learn/overviews/ton-blockchain) to understand this tutorial.

:::info MAINNET DEVELOPMENT IS ESSENTIAL   
Working with the TON Testnet often leads to deployment errors, difficulty tracking transactions, and unstable network functionality. Therefore, it could be beneficial to complete most development on the TON Mainnet to potentially avoid these issues, which might be necessary to reduce the number of transactions and thereby possibly minimize fees.
:::

## 💿 Source Code
All code examples used in this tutorial can be found in the following [GitHub repository](https://github.com/aSpite/wallet-tutorial).


## ✍️ What You Need To Get Started

- Ensure NodeJS is installed.
- Specific Ton libraries are required and include: @ton/ton 13.5.1+, @ton/core 0.49.2+ and @ton/crypto 3.2.0+.

**OPTIONAL**: If you prefer to use GO or Python instead JS, it is  necessary to install the [tonutils-go](https://github.com/xssnick/tonutils-go) library or [pytoniq](https://github.com/yungwine/pytoniq) to conduct development on TON. These libraries will be used in this tutorial for the GO and Python versions.


<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```bash
npm i --save @ton/ton @ton/core @ton/crypto
```

</TabItem>
<TabItem value="go" label="Golang">

```bash
go get github.com/xssnick/tonutils-go
go get github.com/xssnick/tonutils-go/adnl
go get github.com/xssnick/tonutils-go/address
```

</TabItem>
<TabItem value="python" label="Python">

```bash
pip3 install pytoniq
```

</TabItem>
</Tabs>

## ⚙ Set Your Environment

In order to create a TypeScript project it's necessary to conduct the following steps in order:
1. Create an empty folder (which we’ll name WalletsTutorial).
2. Open the project folder using the CLI.
3. Use the following commands to set up your project:
```bash
npm init -y
npm install typescript @types/node ts-node nodemon --save-dev
npx tsc --init --rootDir src --outDir build \ --esModuleInterop --target es2020 --resolveJsonModule --lib es6 \ --module commonjs --allowJs true --noImplicitAny false --allowSyntheticDefaultImports true --strict false
```
:::info
To help us carry out the next process a `ts-node` is used to execute TypeScript code directly without precompiling. `nodemon` is used to restart the node application automatically when file changes in the directory are detected.
:::
4. Next, remove these lines from `tsconfig.json`:
```json
  "files": [
    "\\",
    "\\"
  ]
```
5. Then, create a `nodemon.json` config in your project root with the following content:
```json
{
  "watch": ["src"],
  "ext": ".ts,.js",
  "ignore": [],
  "exec": "npx ts-node ./src/index.ts"
}
```
6. Add this script to `package.json` instead of "test", which is added when the project is created:
```json
"start:dev": "npx nodemon"
```
7. Create `src` folder in the project root and `index.ts` file in this folder.
8. Next, the following code should be added:
```ts
async function main() {
  console.log("Hello, TON!");
}

main().finally(() => console.log("Exiting..."));
```
9. Run the code using terminal:
```bash
npm run start:dev
```
10. Finally, the console output will appear.

![](/img/docs/how-to-wallet/wallet_1.png)

:::tip Blueprint
The TON Community created an excellent tool for automating all development processes (deployment, contract writing, testing) called [Blueprint](https://github.com/ton-org/blueprint). However, we will not be needing such a powerful tool, so it is suggested that the instructions above are followed.
:::

**OPTIONAL: ** When using Golang, follow these instructions::

1. Install the GoLand IDE.
2. Create a project folder and `go.mod` file using the following content (the **version of Go** may need to be changed to conduct this process if the current version being used is outdated):
```
module main

go 1.20
```
3. Type the following command into the terminal:
```bash
go get github.com/xssnick/tonutils-go
```
4. Create the `main.go` file in the root of your project with following content:
```go
package main

import (
	"log"
)

func main() {
	log.Println("Hello, TON!")
}
```
5. Change the name of the module in the `go.mod` to `main`.
6. Run the code above until the output in the terminal is displayed.

:::info
It is also possible to use another IDE since GoLand isn’t free, but it is preferred.
:::

:::warning IMPORTANT
All coding components should be added to the `main` function that was created in the [⚙ Set Your Environment](/develop/smart-contracts/wallets/overview#-set-your-environment) section.

Additionally, only the imports required for a specific code section will be specified in each new section and new imports will need to be added and combined with old ones.  
:::

## 🚀  Let's Get Started!

In this tutorial we’ll learn which wallets (version’s 3 and 4) are most often used on TON Blockchain and get acquainted with how their smart contracts work. This will allow developers to better understand the different messages types on the TON platform to make it simpler to create messages, send them to the blockchain, deploy wallets, and eventually, be able to work with high-load wallets.

Our main task is to build messages using various objects and functions for @ton/ton, @ton/core, @ton/crypto (ExternalMessage, InternalMessage, Signing etc.) to understand what messages look like on a bigger scale. To carry out this process we'll make use of two main wallet versions (v3 and v4) because of the fact that exchanges, non-custodial wallets, and most users only used these specific versions.

:::note
There may be occasions in this tutorial when there is no explanation for particular details. In these cases, more details will be provided in later stages of this tutorial.

**IMPORTANT:** Throughout this tutorial [wallet v3 code](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/wallet3-code.fc) is used to better understand the wallet development process. It should be noted that version v3 has two sub-versions: r1 and r2. Currently, only the second version is being used, this means that when we refer to v3 in this document it means v3r2.
:::

1. [Wallet structure](/develop/smart-contracts/wallets/structure)
2. [Working With Wallet Smart Contracts](/develop/smart-contracts/wallets/messages)
3. [Deploying a Wallet](/develop/smart-contracts/wallets/deploying)
4. [High-Load Wallet](/develop/smart-contracts/wallets/highload)

## 🏁 Conclusion

This tutorial provided us with a better understanding of how different wallet types operate on TON Blockchain. It also allowed us to learn how to create external and internal messages without using predefined library methods.

This helps us to be independent of using libraries and to understand the structure of TON Blockchain in a more in-depth way. We also learned how to use high-load wallets and analyzed many details to do with different data types and various operations.

## 🧩 Next Steps

Reading the documentation provided above is a complex undertaking and it’s difficult to understand the entirety of the TON platform. However, it is a good exercise for those passionate about building on the TON. Another suggestion is to begin learning about how to write smart contracts on TON by consulting the following resources: [FunC Overview](https://docs.ton.org/develop/func/overview), [Best Practices](https://docs.ton.org/develop/smart-contracts/guidelines), [Examples of Smart Contracts](https://docs.ton.org/develop/smart-contracts/examples), [FunC Cookbook](https://docs.ton.org/develop/func/cookbook)

Additionally, it is recommended that readers familiarize themselves with the following documents in more detail: [ton.pdf](https://docs.ton.org/ton.pdf) and [tblkch.pdf](https://ton.org/tblkch.pdf) documents.

## 📬 About the Author

If you have any questions, comments, or suggestions please reach out to the author of this documentation section on [Telegram](https://t.me/aspite) (@aSpite or @SpiteMoriarty) or [GitHub](https://github.com/aSpite).

## 📖 See Also

- Wallets' source code: [V3](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/wallet3-code.fc), [V4](https://github.com/ton-blockchain/wallet-contract/blob/main/func/wallet-v4-code.fc), [High-load](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/highload-wallet-v2-code.fc)

- Useful concept documents(may include outdated information): [ton.pdf](https://docs.ton.org/ton.pdf), [tblkch.pdf](https://ton.org/tblkch.pdf), [tvm.pdf](https://ton.org/tvm.pdf)

The main sources of code:

  - [@ton/ton (JS/TS)](https://github.com/ton-org/ton)
  - [@ton/core (JS/TS)](https://github.com/ton-org/ton-core)
  - [@ton/crypto (JS/TS)](https://github.com/ton-org/ton-crypto)
  - [tonutils-go (GO)](https://github.com/xssnick/tonutils-go).

Official documentation:

  - [Internal messages](/develop/smart-contracts/guidelines/internal-messages)

  - [External messages](/develop/smart-contracts/guidelines/external-messages)

  - [Types of Wallet Contracts](/participate/wallets/contracts#wallet-v4)
  
  - [TL-B](/develop/data-formats/tl-b-language)

  - [Blockchain of Blockchains](https://docs.ton.org/learn/overviews/ton-blockchain)

External references:

- [Ton Deep](https://github.com/xssnick/ton-deep-doc)

- [Block.tlb](https://github.com/ton-blockchain/ton/blob/master/crypto/block/block.tlb)

- [Standards in TON](https://github.com/ton-blockchain/TEPs)
