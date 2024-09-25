import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# 👛 Deploying a Wallet

We have learned the basics of creating messages, which will now be helpful for deploying the wallet. In the past, we have deployed wallet via wallet app, but in this case we’ll need to deploy our wallet manually.

In this section we’ll go over how to create a wallet (wallet v3) from scratch. You’ll learn how to compile the code for a wallet smart contract, generate a mnemonic phrase, receive a wallet address, and deploy a wallet using external messages and State Init (state initialization).

## Generating a Mnemonic

The first thing needed to correctly create a wallet is to retrieve a `private` and `public` key. To accomplish this task it is necessary to generate a mnemonic seed phrase and then extract private and public keys using cryptographic libraries. 

This is accomplished as follows:


<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { mnemonicToWalletKey, mnemonicNew } from '@ton/crypto';

// const mnemonicArray = 'put your mnemonic'.split(' ') // get our mnemonic as array
const mnemonicArray = await mnemonicNew(24); // 24 is the number of words in a seed phrase
const keyPair = await mnemonicToWalletKey(mnemonicArray); // extract private and public keys from mnemonic
console.log(mnemonicArray) // if we want, we can print our mnemonic
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
	"crypto/ed25519"
	"crypto/hmac"
	"crypto/sha512"
	"log"
	"github.com/xssnick/tonutils-go/ton/wallet"
	"golang.org/x/crypto/pbkdf2"
	"strings"
)

// mnemonic := strings.Split("put your mnemonic", " ") // get our mnemonic as array
mnemonic := wallet.NewSeed() // get new mnemonic

// The following three lines will extract the private key using the mnemonic phrase. We will not go into cryptographic details. It has all been implemented in the tonutils-go library, but it immediately returns the finished object of the wallet with the address and ready methods. So we’ll have to write the lines to get the key separately. Goland IDE will automatically import all required libraries (crypto, pbkdf2 and others).
mac := hmac.New(sha512.New, []byte(strings.Join(mnemonic, " "))) 
hash := mac.Sum(nil)
k := pbkdf2.Key(hash, []byte("TON default seed"), 100000, 32, sha512.New) // In TON libraries "TON default seed" is used as salt when getting keys
// 32 is a key len 

privateKey := ed25519.NewKeyFromSeed(k) // get private key
publicKey := privateKey.Public().(ed25519.PublicKey) // get public key from private key
log.Println(publicKey) // print publicKey so that at this stage the compiler does not complain that we do not use our variable
log.Println(mnemonic) // if we want, we can print our mnemonic
```

</TabItem>
</Tabs>

The private key is needed to sign messages and the public key is stored in the wallet’s smart contract.

:::danger IMPORTANT
It is necessary to output the generated mnemonic seed phrase to the console then save and use it (as detailed in the previous section) in order to use the same key pair each time the wallet’s code is run.
:::

## Subwallet IDs

One of the most notable benefits of wallets being smart contracts is the ability to create **a vast number of wallets** using just one private key. This is because the addresses of smart contracts on TON Blockchain are computed using several factors including the `stateInit`. The stateInit contains the `code` and `initial data`, which is stored in the blockchain’s smart contract storage.

By changing just one bit within the stateInit, a different address can be generated. That is why the `subwallet_id` was initially created. The  `subwallet_id` is stored in the contract storage and it can be used to create many different wallets (with different subwallet IDs) with one private key. This functionality can be very useful when integrating various wallet types with centralized service such as exchanges.

The default subwallet_id value is `698983191` according to the [line of code](https://github.com/ton-blockchain/ton/blob/4b940f8bad9c2d3bf44f196f6995963c7cee9cc3/tonlib/tonlib/TonlibClient.cpp#L2420) below taken from the TON Blockchain’s source code:

```cpp
res.wallet_id = td::as<td::uint32>(res.config.zero_state_id.root_hash.as_slice().data());
```

It is possible to retrieve genesis block information (zero_state) from the [configuration file](https://ton.org/global-config.json). Understanding the complexities and details of this is not necessary but it's important to remember that the default value of the `subwallet_id` is `698983191`.

Each wallet contract checks the subwallet_id field for external messages to avoid instances when requests were sent to wallet with another ID:

```func
var (subwallet_id, valid_until, msg_seqno) = (cs~load_uint(32), cs~load_uint(32), cs~load_uint(32));
var (stored_seqno, stored_subwallet, public_key) = (ds~load_uint(32), ds~load_uint(32), ds~load_uint(256));
throw_unless(34, subwallet_id == stored_subwallet);
```

We will need to add the above value to the initial data of the contract, so the variable needs to be saved as follows:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
const subWallet = 698983191;
```

</TabItem>
<TabItem value="go" label="Golang">

```go
var subWallet uint64 = 698983191
```

</TabItem>
</Tabs>

## Compiling Wallet Code

Now that we have the private and public keys and the subwallet_id clearly defined we need to compile the wallet code. To accomplish this, we’ll use the [wallet v3 code](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/wallet3-code.fc) from the official repository.

To compile wallet code it is necessary to use the [@ton-community/func-js](https://github.com/ton-community/func-js) library.
Using this library it allows us to compile FunC code and retrieve a cell containing the code. To get started, it is necessary to install the library and save (--save) it to the `package.json` as follows:

```bash
npm i --save @ton-community/func-js
```

We’ll only use JavaScript to compile code, as the libraries for compiling code are JavaScript based.
However, after compiling is finalized, as long as we have the **base64 output** of our cell, it is possible to use this compiled code in languages such as Go and others.

First, we need to create two files: `wallet_v3.fc` and `stdlib.fc`. The compiler works with the stdlib.fc library. All necessary and basic functions, which correspond with the `asm` instructions were created in the library. The stdlib.fc file can be downloaded [here](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/stdlib.fc). In the  `wallet_v3.fc` file it is necessary to copy the code above. 

Now we have the following structure for the project we are creating:

```
.
├── src/
│   ├── main.ts
│   ├── wallet_v3.fc
│   └── stdlib.fc
├── nodemon.json
├── package-lock.json
├── package.json
└── tsconfig.json
```

:::info
It’s fine if your IDE plugin conflicts with the `() set_seed(int) impure asm "SETRAND";` in the `stdlib.fc` file.
:::

Remember to add the following line to the beginning of the `wallet_v3.fc` file to indicate that the functions from the stdlib will be used below:

```func
#include "stdlib.fc";
```

Now let’s write code to compile our smart contract and run it using the `npm run start:dev`:

```js
import { compileFunc } from '@ton-community/func-js';
import fs from 'fs'; // we use fs for reading content of files
import { Cell } from '@ton/core';

const result = await compileFunc({
targets: ['wallet_v3.fc'], // targets of your project
sources: {
    "stdlib.fc": fs.readFileSync('./src/stdlib.fc', { encoding: 'utf-8' }),
    "wallet_v3.fc": fs.readFileSync('./src/wallet_v3.fc', { encoding: 'utf-8' }),
}
});

if (result.status === 'error') {
console.error(result.message)
return;
}

const codeCell = Cell.fromBoc(Buffer.from(result.codeBoc, "base64"))[0]; // get buffer from base64 encoded BOC and get cell from this buffer

// now we have base64 encoded BOC with compiled code in result.codeBoc
console.log('Code BOC: ' + result.codeBoc);
console.log('\nHash: ' + codeCell.hash().toString('base64')); // get the hash of cell and convert in to base64 encoded string. We will need it further
```

The result will be the following output in the terminal:

```text
Code BOC: te6ccgEBCAEAhgABFP8A9KQT9LzyyAsBAgEgAgMCAUgEBQCW8oMI1xgg0x/TH9MfAvgju/Jj7UTQ0x/TH9P/0VEyuvKhUUS68qIE+QFUEFX5EPKj+ACTINdKltMH1AL7AOgwAaTIyx/LH8v/ye1UAATQMAIBSAYHABe7Oc7UTQ0z8x1wv/gAEbjJftRNDXCx+A==

Hash: idlku00WfSC36ujyK2JVT92sMBEpCNRUXOGO4sJVBPA=
```

Once this is completed it is possible to retrieve the same cell (using the base64 encoded output) with our wallet code using other libraries and languages:

<Tabs groupId="code-examples">
<TabItem value="go" label="Golang">

```go
import (
  "encoding/base64"
  "github.com/xssnick/tonutils-go/tvm/cell"
)

base64BOC := "te6ccgEBCAEAhgABFP8A9KQT9LzyyAsBAgEgAgMCAUgEBQCW8oMI1xgg0x/TH9MfAvgju/Jj7UTQ0x/TH9P/0VEyuvKhUUS68qIE+QFUEFX5EPKj+ACTINdKltMH1AL7AOgwAaTIyx/LH8v/ye1UAATQMAIBSAYHABe7Oc7UTQ0z8x1wv/gAEbjJftRNDXCx+A==" // save our base64 encoded output from compiler to variable
codeCellBytes, _ := base64.StdEncoding.DecodeString(base64BOC) // decode base64 in order to get byte array
codeCell, err := cell.FromBOC(codeCellBytes) // get cell with code from byte array
if err != nil { // check if there are any error
  panic(err) 
}

log.Println("Hash:", base64.StdEncoding.EncodeToString(codeCell.Hash())) // get the hash of our cell, encode it to base64 because it has []byte type and output to the terminal
```

</TabItem>
</Tabs>



The result will be the following output in the terminal:

```text
idlku00WfSC36ujyK2JVT92sMBEpCNRUXOGO4sJVBPA=
```

After the above processes are complete it is confirmed that the correct code is being used within our cell because the hashes match.

## Creating the State Init for Deployment

Before building a message it is important to understand what a State Init is. First let’s go through the [TL-B scheme](https://github.com/ton-blockchain/ton/blob/24dc184a2ea67f9c47042b4104bbb4d82289fac1/crypto/block/block.tlb#L141-L143):

Option | Explanation
:---: | :---:
split_depth | This option is intended for highly loaded smart contracts that can be split and located on several [shardchains](/learn/overviews/ton-blockchain#many-accountchains-shards).  More information detailing how this works can be found in the [tblkch.pdf](https://ton.org/tblkch.pdf) (4.1.6).  Only a `0` bit is stored since it is being used only within a wallet smart contract.
special | Used for TicTok. These smart contracts are automatically called for each block and are not needed for regular smart contracts. Information about this can be found in [this section](/develop/data-formats/transaction-layout#tick-tock) or in [tblkch.pdf](https://ton.org/tblkch.pdf) (4.1.6). Only a `0` bit is stored within this specification because we do not need such a function.
code | `1` bit means the presence of the smart contract code as a reference.
data | `1` bit means the presence of the smart contract data as a reference.
library | A library that operates on the [masterchain](/learn/overviews/ton-blockchain#masterchain-blockchain-of-blockchains)  and can be used by different smart contracts. This will not be used for wallet, so its bit is set to `0`. Information about this can be found in [tblkch.pdf](https://ton.org/tblkch.pdf) (1.8.4).

Next we’ll prepare the `initial data`, which will be present in our contract’s storage immediately after deployment:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { beginCell } from '@ton/core';

const dataCell = beginCell()
  .storeUint(0, 32) // Seqno
  .storeUint(698983191, 32) // Subwallet ID
  .storeBuffer(keyPair.publicKey) // Public Key
  .endCell();
```

</TabItem>
<TabItem value="go" label="Golang">

```go
dataCell := cell.BeginCell().
  MustStoreUInt(0, 32). // Seqno
  MustStoreUInt(698983191, 32). // Subwallet ID
  MustStoreSlice(publicKey, 256). // Public Key
  EndCell()
```

</TabItem>
</Tabs>

At this stage, both the contract `code` and its `initial data` is present. With this data, we can produce our **wallet address**. The address of the wallet depends on the State Init, which includes the code and initial data.

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { Address } from '@ton/core';

const stateInit = beginCell()
  .storeBit(0) // No split_depth
  .storeBit(0) // No special
  .storeBit(1) // We have code
  .storeRef(codeCell)
  .storeBit(1) // We have data
  .storeRef(dataCell)
  .storeBit(0) // No library
  .endCell();

const contractAddress = new Address(0, stateInit.hash()); // get the hash of stateInit to get the address of our smart contract in workchain with ID 0
console.log(`Contract address: ${contractAddress.toString()}`); // Output contract address to console
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
  "github.com/xssnick/tonutils-go/address"
)

stateInit := cell.BeginCell().
  MustStoreBoolBit(false). // No split_depth
  MustStoreBoolBit(false). // No special
  MustStoreBoolBit(true). // We have code
  MustStoreRef(codeCell).
  MustStoreBoolBit(true). // We have data
  MustStoreRef(dataCell).
  MustStoreBoolBit(false). // No library
  EndCell()

contractAddress := address.NewAddress(0, 0, stateInit.Hash()) // get the hash of stateInit to get the address of our smart contract in workchain with ID 0
log.Println("Contract address:", contractAddress.String()) // Output contract address to console
```

</TabItem>
</Tabs>

Using the State Init, we can now build the message and send it to the blockchain. To carry out this process **a minimum wallet balance of 0.1 TON** (the balance can be less, but this amount is guaranteed to be sufficient) is required. To accomplish this, we’ll need to run the code mentioned earlier in the tutorial, get the correct wallet address and send 0.1 TON to this address.

Let’s start with building the message similar to the one we built **in the previous section**:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { sign } from '@ton/crypto';
import { toNano } from '@ton/core';

const internalMessageBody = beginCell()
  .storeUint(0, 32)
  .storeStringTail("Hello, TON!")
  .endCell();

const internalMessage = beginCell()
  .storeUint(0x10, 6) // no bounce
  .storeAddress(Address.parse("put your first wallet address from were you sent 0.1 TON"))
  .storeCoins(toNano("0.03"))
  .storeUint(1, 1 + 4 + 4 + 64 + 32 + 1 + 1) // We store 1 that means we have body as a reference
  .storeRef(internalMessageBody)
  .endCell();

// message for our wallet
const toSign = beginCell()
  .storeUint(subWallet, 32)
  .storeUint(Math.floor(Date.now() / 1e3) + 60, 32)
  .storeUint(0, 32) // We put seqno = 0, because after deploying wallet will store 0 as seqno
  .storeUint(3, 8)
  .storeRef(internalMessage);

const signature = sign(toSign.endCell().hash(), keyPair.secretKey);
const body = beginCell()
  .storeBuffer(signature)
  .storeBuilder(toSign)
  .endCell();
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
  "github.com/xssnick/tonutils-go/tlb"
  "time"
)

internalMessageBody := cell.BeginCell().
  MustStoreUInt(0, 32).
  MustStoreStringSnake("Hello, TON!").
  EndCell()

internalMessage := cell.BeginCell().
  MustStoreUInt(0x10, 6). // no bounce
  MustStoreAddr(address.MustParseAddr("put your first wallet address from were you sent 0.1 TON")).
  MustStoreBigCoins(tlb.MustFromTON("0.03").NanoTON()).
  MustStoreUInt(1, 1 + 4 + 4 + 64 + 32 + 1 + 1). // We store 1 that means we have body as a reference
  MustStoreRef(internalMessageBody).
  EndCell()

// message for our wallet
toSign := cell.BeginCell().
  MustStoreUInt(subWallet, 32).
  MustStoreUInt(uint64(time.Now().UTC().Unix()+60), 32).
  MustStoreUInt(0, 32). // We put seqno = 0, because after deploying wallet will store 0 as seqno
  MustStoreUInt(3, 8).
  MustStoreRef(internalMessage)

signature := ed25519.Sign(privateKey, toSign.EndCell().Hash())
body := cell.BeginCell().
  MustStoreSlice(signature, 512).
  MustStoreBuilder(toSign).
	EndCell()
```

</TabItem>
</Tabs>

After this is completed the result is the correct State Init and Message Body.

## Sending An External Message

The **main difference** will be in the presence of the external message, because the State Init is stored to help carry out correct contract deployment. Since the contract does not have its own code yet, it cannot process any internal messages. Therefore, next we send its code and the initial data **after it is successfully deployed so it can process our message** with "Hello, TON!" comment:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
const externalMessage = beginCell()
  .storeUint(0b10, 2) // indicate that it is an incoming external message
  .storeUint(0, 2) // src -> addr_none
  .storeAddress(contractAddress)
  .storeCoins(0) // Import fee
  .storeBit(1) // We have State Init
  .storeBit(1) // We store State Init as a reference
  .storeRef(stateInit) // Store State Init as a reference
  .storeBit(1) // We store Message Body as a reference
  .storeRef(body) // Store Message Body as a reference
  .endCell();
```

</TabItem>
<TabItem value="go" label="Golang">

```go
externalMessage := cell.BeginCell().
  MustStoreUInt(0b10, 2). // indicate that it is an incoming external message
  MustStoreUInt(0, 2). // src -> addr_none
  MustStoreAddr(contractAddress).
  MustStoreCoins(0). // Import fee
  MustStoreBoolBit(true). // We have State Init
  MustStoreBoolBit(true).  // We store State Init as a reference
  MustStoreRef(stateInit). // Store State Init as a reference
  MustStoreBoolBit(true). // We store Message Body as a reference
  MustStoreRef(body). // Store Message Body as a reference
  EndCell()
```

</TabItem>
</Tabs>

Finally, we can send our message to the blockchain to deploy our wallet and use it.

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { TonClient } from '@ton/ton';

const client = new TonClient({
  endpoint: "https://toncenter.com/api/v2/jsonRPC",
  apiKey: "put your api key" // you can get an api key from @tonapibot bot in Telegram
});

client.sendFile(externalMessage.toBoc());
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
  "context"
  "github.com/xssnick/tonutils-go/liteclient"
  "github.com/xssnick/tonutils-go/tl"
  "github.com/xssnick/tonutils-go/ton"
)

connection := liteclient.NewConnectionPool()
configUrl := "https://ton-blockchain.github.io/global.config.json"
err := connection.AddConnectionsFromConfigUrl(context.Background(), configUrl)
if err != nil {
  panic(err)
}
client := ton.NewAPIClient(connection)

var resp tl.Serializable
err = client.Client().QueryLiteserver(context.Background(), ton.SendMessage{Body: externalMessage.ToBOCWithFlags(false)}, &resp)
if err != nil {
  log.Fatalln(err.Error())
  return
}
```

</TabItem>
</Tabs>

Note that we have sent an internal message using mode `3`. If it is necessary to repeat the deployment of the same wallet, **the smart contract can be destroyed**. To accomplish this, set the mode correctly by adding 128 (take the entire balance of the smart contract) + 32 (destroy the smart contract) which will = `160` to retrieve the remaining TON balance and deploy the wallet again.

It's important to note that for each new transaction the **seqno will need to be increased by one**.

:::info
The contract code we used is [verified](https://tonscan.org/tx/BL9T1i5DjX1JRLUn4z9JOgOWRKWQ80pSNevis26hGvc=), so you can see an example [here](https://tonscan.org/address/EQDBjzo_iQCZh3bZSxFnK9ue4hLTOKgsCNKfC8LOUM4SlSCX#source).
:::