import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# 🔥 High-Load Wallet

## 🔥 High-Load Wallet V3

When working with many messages in a short period, there is a need for special wallet called High-Load Wallet. High-Load Wallet V2 was the main wallet on TON for a long time, but you had to be very careful with it. Otherwise, you could [lock all funds](https://t.me/tonstatus/88). 

[With the advent of High-Load Wallet V3](https://github.com/ton-blockchain/highload-wallet-contract-v3), this problem has been solved at the contract architecture level and consumes less gas. This chapter will cover the basics of High-Load Wallet V3 and important nuances to remember.

:::note
We will work [with a slightly modified version of Wrapper](https://github.com/aSpite/highload-wallet-contract-v3/blob/main/wrappers/HighloadWalletV3.ts) for the contract, as it protects against some non-obvious mistakes.
:::note


### Storage Structure

First of all, [TL-B schema](https://github.com/ton-blockchain/highload-wallet-contract-v3/blob/d58c31e82315c34b4db55942851dd8d4153975c5/contracts/scheme.tlb#L1C1-L3C21) will help us in learning the structure of the contract storage:

```
storage$_ public_key:bits256 subwallet_id:uint32 old_queries:(HashmapE 14 ^Cell)
          queries:(HashmapE 14 ^Cell) last_clean_time:uint64 timeout:uint22
          = Storage;
```

:::tip TL-B
You can read more about TL-B [here](/develop/data-formats/tl-b-language).
:::

In the contract storage, we can find the following fields:

| Field | Description |
| :---: | :---: |
| public_key | Public key of the contract. |
| subwallet_id | [Wallet ID](#subwallet-ids). It allows you to create many wallets using the same public key. |
| old_queries | Old queries that have already been processed and are outdated. They are moved here after each timeout. |
| queries | Queries that have been processed but are not yet outdated. |
| last_clean_time | The time of the last cleanup. If `last_clean_time < (now() - timeout)`, old queries are moved to `old_queries`. If `last_clean_time < (now() - 2 * timeout)`, both `old_queries` and `queries` are cleared. |
| timeout | The time after which queries are moved to `old_queries`. |

We will discuss more about working with processed queries in [Replay Protection](#replay-protection).

### Shifts and Bits Numbers as Query ID

The Query ID is a number that consists of two parts: shift and bit_number:

```func.
int shift = msg_inner_slice~load_uint(KEY_SIZE);
int bit_number = msg_inner_slice~load_uint(BIT_NUMBER_SIZE);
```

The basic idea behind this is that each Query ID now only takes up 1 bit in the dictionary while not increasing gas consumption most of the time.

To start, the contract, using shift, tries to get the cell at that index in the `old_queries` dictionary:

```func
(cell value, int found) = old_queries.udict_get_ref?(KEY_SIZE, shift);
```

If such a cell is found, it skips `bit_number` bits to reach the bit with index `bit_number` (it is important to understand the difference between bit_number as a quantity and bit_number as an index). If such a bit is found, it means that a query with such a Query ID has already been processed, and an error is thrown:

```func
if (found) {
    slice value_slice = value.begin_parse();
    value_slice~skip_bits(bit_number);
    throw_if(error::already_executed, value_slice.preload_int(1));
}
```

The next step is to search the `queries` dictionary:

```func
(cell value, int found) = queries.udict_get_ref?(KEY_SIZE, shift);
```

If such a cell is found, the contract cuts it into 2 parts: `0...bit_number-1` (head) and `bit_number...1023` (tail). Then, one bit is read from the beginning of the tail (the number of this bit is equal to the `bit_number` variable if you start counting from 0, i.e. it is the index of the required bit). If it is positive, the request with such a Query ID has already been processed, and an error is thrown. Otherwise, the bit is set to 1, and all the pieces are merged into one cell again and written back into the `queries` dictionary:

```func
builder new_value = null();
if (found) {
    slice value_slice = value.begin_parse();
    (slice tail, slice head) = value_slice.load_bits(bit_number);
    throw_if(error::already_executed, tail~load_int(1));
    new_value = begin_cell().store_slice(head).store_true().store_slice(tail);
} else {
    new_value = begin_cell().store_zeroes(bit_number).store_true().store_zeroes(CELL_BITS_SIZE - bit_number - 1);
}
```

:::note
If you [familiarize yourself](https://docs.ton.org/learn/tvm-instructions/instructions) with the operation of the `LDSLICEX` opcode (the load_bits function uses this opcode), you will notice that the read data is returned first (head) and only then the remaining data (tail), but they are in reverse order in the contract code.

In fact, they go in reverse order, because in stdlib in the function signature, the returned data [go in reverse order](https://github.com/ton-blockchain/highload-wallet-contract-v3/blob/d58c31e82315c34b4db55942851dd8d4153975c5/contracts/imports/stdlib.fc#L321): `(slice, slice) load_bits(slice s, int len) asm(s len -> 1 0) "LDSLICEX";`. Here `-> 1 0` means to return the argument with index 1 (tail) first, and then 0 (head).
:::

So in effect we are working with a matrix where `shift` is the row index and `bit_number` is the column index. This allows us to store up to 1023 queries in a single cell, which means that gas consumption will only increase every 1023 queries due to adding a new cell to the dictionary. It is important to realize that this will be done if the values grow sequentially, not randomly, so it is necessary to properly increase Query ID, [using a special class for this](https://github.com/aSpite/highload-wallet-contract-v3/blob/main/wrappers/HighloadQueryId.ts).

This approach allows storing a huge number of requests per timeout (1023 \* 8192 = 8,380,416), but you may notice that [the class HighloadQueryId supports 8,380,415](https://github.com/ton-blockchain/highload-wallet-contract-v3/blob/d58c31e82315c34b4db55942851dd8d4153975c5/wrappers/HighloadQueryId.ts#L32). This is to ensure that there will always be 1 bit left for one emergency timeout request if the entire limit is exhausted. This value is set because of the [limit on the maximum possible number of cells in an account stack](https://github.com/ton-blockchain/ton/blob/5c392e0f2d946877bb79a09ed35068f7b0bd333a/crypto/block/mc-config.h#L395) on the blockchain (as of this writing).

For every cell that can hold 1023 requests, 2 cells in the dictionary are spent (one to store the key, the other for the value). If we take the current maximum shift value, the theoretical maximum is 8192 \* 2 \* 2 (we have two dictionaries: queries and old_queries) = 32,768 cells. If you increase the key size by a bit, it will no longer fit within the current limits.

:::info
Earlier in High-Load V2, each Query ID (64-bit) was stored in a separate cell in the dictionary and was a union of 32-bit fields `expire_at` and `query_id`. This led to a very fast growth in gas consumption when clearing old queries.
:::

### Replay Protection

As we know that external messages in TON [have no sender and can be sent by anyone in the network](#replay-protection---seqno), it is important to have a list of processed requests to avoid re-processing. For this purpose, High-Load Wallet V3 uses the `queries` and `old_queries` dictionaries and the `last_clean_time` and `timeout` values.

After the contract has completely retrieved all the data it needs from its storage, it checks to see when the last query dictionary cleanup occurred. If it was more than the `timeout` time ago, the contract moves all queries from queries to old_queries. If the last cleanup was more than `timeout * 2` times ago, the contract cleans up old_queries in addition:

```func
if (last_clean_time < (now() - timeout)) {
    (old_queries, queries) = (queries, null());
    if (last_clean_time < (now() - (timeout * 2))) {
        old_queries = null();
    }
    last_clean_time = now();
}
```

The reason for this is that the contract does not keep track of when exactly which request was executed. This means that if `timeout` is 3 hours, but the last request was executed one minute before reaching 3 hours, the request will be considered outdated one minute later, despite the 3-hour timeout. To solve this problem, the second dictionary stores the same queries for at least that much more time.

Theoretically, a query has a lifetime from `timeout` to `timeout * 2`, which means that when tracking which queries are outdated, it is good practice to wait at least `timeout * 2` times to see if the query is obsolete.

### Guaranteed Error-Free Action Phase

Once all the checks and cleanups have been completed, the contract can accept the message, make changes to its storage, and call the commit function, which will consider the compute phase a success even if some error is thrown next:

```func
accept_message();

queries~udict_set_ref(KEY_SIZE, shift, new_value.end_cell());

set_data(begin_cell()
    .store_uint(public_key, PUBLIC_KEY_SIZE)
    .store_uint(subwallet_id, SUBWALLET_ID_SIZE)
    .store_dict(old_queries)
    .store_dict(queries)
    .store_uint(last_clean_time, TIMESTAMP_SIZE)
    .store_uint(timeout, TIMEOUT_SIZE)
    .end_cell());


commit();
```

This is done so that when executing further code if there is an error in the message the user is trying to send, the contract does not return to its previous state. Otherwise, the external will remain valid and can be accepted several times, resulting in wasted balance.

However, another issue must be addressed - possible errors during the **Action Phase**. Although we have a flag to ignore the mistakes (2) when sending a message, it doesn't work in all cases, so we need to ensure that no errors occur during this phase, which could cause the state to roll back and make `commit()` meaningless. 

For this reason, instead of sending all messages directly, the contract sends itself a message with the `internal_transfer` opcode. This message is parsed in detail by the contract to ensure that no Action Phase error occurs:

```func
throw_if(error::invalid_message_to_send, message_slice~load_uint(1)); ;; int_msg_info$0
int msg_flags = message_slice~load_uint(3); ;; ihr_disabled:Bool bounce:Bool bounced:Bool
if (is_bounced(msg_flags)) {
    return ();
}
slice message_source_adrress = message_slice~load_msg_addr(); ;; src
throw_unless(error::invalid_message_to_send, is_address_none(message_source_adrress));
message_slice~load_msg_addr(); ;; dest
message_slice~load_coins(); ;; value.coins
message_slice = message_slice.skip_dict(); ;; value.other extra-currencies
message_slice~load_coins(); ;; ihr_fee
message_slice~load_coins(); ;; fwd_fee
message_slice~skip_bits(64 + 32); ;; created_lt:uint64 created_at:uint32
int maybe_state_init = message_slice~load_uint(1);
throw_if(error::invalid_message_to_send, maybe_state_init); ;; throw if state-init included (state-init not supported)
int either_body = message_slice~load_int(1);
if (either_body) {
    message_slice~load_ref();
    message_slice.end_parse();
}
```

If any problem occurs while reading the data, it will still be Compute Phase. However, due to the presence of `commit()` this is not a problem and the transaction will still be considered a success. If all data has been read successfully, this is a guarantee that the Action Phase will pass without errors, as these checks cover all cases where the `IGNORE_ERRORS` (2) flag fails. The contract can then complete its work by sending a message:

```func
;; send message with IGNORE_ERRORS flag to ignore errors in the action phase

send_raw_message(message_to_send, send_mode | SEND_MODE_IGNORE_ERRORS);
```

### Internal Transfer

After `internal_transfer` reaches the contract, it loads the list of actions, sets them in the c5 register, and then applies `set_code` to protect against accidental code changes, which is also an action. Because of this, the number of messages that can be sent is 254 rather than 255, which is the limit on the blockchain. However, the contract can call itself to send more messages, which we will discuss later:

```func
if (op == op::internal_transfer) {
    in_msg_body~skip_query_id();
    cell actions = in_msg_body.preload_ref();
    cell old_code = my_code();
    set_actions(actions);
    set_code(old_code); ;; prevent to change smart contract code
    return ();
}
```

When dealing with `internal_transfer` there is one important nuance. As we have discussed above, the contract sends a message to itself, but that message is entirely collected on the user side. The problem is that you need to correctly count how much TON will be attached to the message. 

In the wrapper in the official repository this field is optional and if the user does not specify it, [mode becomes 128](https://github.com/ton-blockchain/highload-wallet-contract-v3/blob/d58c31e82315c34b4db55942851dd8d4153975c5/wrappers/HighloadWalletV3.ts#L115), which means that the entire balance is sent. The problem is that in such a case there is a **edge case**.

Let's imagine that we want to send out a lot of tokens. After sending out the rest of the TON are returned to our wallet, since we set our address in the `response_destination` field. We start sending out multiple externals at the same time and the following situation occurs:

1. External message A is received, processed and sends the entire contract balance via `internal_transfer`.
2. Before external message B reaches, part of the commissions from the already completed token sent reaches. Hence, the non-empty contract balance allows the entire balance to be sent to internal message B again, but this time, a very small amount of TONs is sent.
3. Internal message A is received, processed. Token sending messages are sent.
4. Before internal message B reaches, external message C manages to reach and sends the entire balance again.
5. When receiving internal message B, the contract has little TON, even if some extra TON from sending tokens will reach and the request fails with exit code = 37 on Action Phase (Insufficient Funds).

Thus the contract displays that the request has been processed when in fact it has not. To avoid this scenario, it is **recommended to always put 1 TON** on `internal_transfer`. Therefore, [we are working with a modified wrapper](#-high-load-wallet-v3) that requires the user to specify the number of TONs. This value will suffice for all cases, since the external message size is limited to 64 KB and a message close to this limit will spend less than 1 TON.

High-Load Wallet V3 can send more than 254 messages, [putting the remaining messages into the 254th message](https://github.com/aSpite/highload-wallet-contract-v3/blob/d4c1752d00b5303782f121a87eb0620d403d9544/wrappers/HighloadWalletV3.ts#L169-L176). This way `internal_transfer` will be processed several times. The wrapper automatically does this, and we won't have to worry about it, but **recommended to take no more than 150 messages at a time** to ensure that even complex messages will fit into an external message.

:::info
Although the external message limit is 64KB, the larger the external, the more likely it is to get lost in delivery, so 150 messages is the optimal solution.
:::

### GET Methods

High-Load Wallet V3 supports the 5 GET methods:

Method | Explanation
:---: | :---:
int get_public_key() | Returns the public key of the contract.
int get_subwallet_id() | Returns the subwallet ID.
int get_last_clean_time() | Returns the time of the last cleaning.
int get_timeout() | Returns the timeout value.
int processed?(int query_id, int need_clean) | Returns whether the query_id has been processed. If need_clean is set to 1, then will first do the cleanup based on `last_clean_time` and `timeout` and then check for query_id in `old_queries` and `queries`.

:::tip
It is recommended to pass `true` for `need_clean` unless the situation requires otherwise since the most current dictionary states will then be returned.
:::

Due to how the Query ID is organized in High-Load Wallet V3, we can send a message with the same Query ID again if it does not arrive without fear of the request being processed twice. 

However, in such a case, we must consider that no more than `timeout` time has elapsed since the first sending attempt. Otherwise, the request may have been processed but already deleted from the dictionaries. Therefore, it is recommended to set `timeout` to no less than an hour and no more than 24 hours.


### Deploying High-Load Wallet V3

To deploy a contract, we need 2 cells: `code` and `date`. For the code, we will use the following cell:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { Cell } from "@ton/core";

const HIGHLOAD_V3_CODE = Cell.fromBoc(Buffer.from('b5ee9c7241021001000228000114ff00f4a413f4bcf2c80b01020120020d02014803040078d020d74bc00101c060b0915be101d0d3030171b0915be0fa4030f828c705b39130e0d31f018210ae42e5a4ba9d8040d721d74cf82a01ed55fb04e030020120050a02027306070011adce76a2686b85ffc00201200809001aabb6ed44d0810122d721d70b3f0018aa3bed44d08307d721d70b1f0201200b0c001bb9a6eed44d0810162d721d70b15800e5b8bf2eda2edfb21ab09028409b0ed44d0810120d721f404f404d33fd315d1058e1bf82325a15210b99f326df82305aa0015a112b992306dde923033e2923033e25230800df40f6fa19ed021d721d70a00955f037fdb31e09130e259800df40f6fa19cd001d721d70a00937fdb31e0915be270801f6f2d48308d718d121f900ed44d0d3ffd31ff404f404d33fd315d1f82321a15220b98e12336df82324aa00a112b9926d32de58f82301de541675f910f2a106d0d31fd4d307d30cd309d33fd315d15168baf2a2515abaf2a6f8232aa15250bcf2a304f823bbf2a35304800df40f6fa199d024d721d70a00f2649130e20e01fe5309800df40f6fa18e13d05004d718d20001f264c858cf16cf8301cf168e1030c824cf40cf8384095005a1a514cf40e2f800c94039800df41704c8cbff13cb1ff40012f40012cb3f12cb15c9ed54f80f21d0d30001f265d3020171b0925f03e0fa4001d70b01c000f2a5fa4031fa0031f401fa0031fa00318060d721d300010f0020f265d2000193d431d19130e272b1fb00b585bf03', 'hex'))[0];
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
	"encoding/hex"
	"log"

	"github.com/xssnick/tonutils-go/tvm/cell"
)

codeb, err := hex.DecodeString("b5ee9c7241021001000228000114ff00f4a413f4bcf2c80b01020120020d02014803040078d020d74bc00101c060b0915be101d0d3030171b0915be0fa4030f828c705b39130e0d31f018210ae42e5a4ba9d8040d721d74cf82a01ed55fb04e030020120050a02027306070011adce76a2686b85ffc00201200809001aabb6ed44d0810122d721d70b3f0018aa3bed44d08307d721d70b1f0201200b0c001bb9a6eed44d0810162d721d70b15800e5b8bf2eda2edfb21ab09028409b0ed44d0810120d721f404f404d33fd315d1058e1bf82325a15210b99f326df82305aa0015a112b992306dde923033e2923033e25230800df40f6fa19ed021d721d70a00955f037fdb31e09130e259800df40f6fa19cd001d721d70a00937fdb31e0915be270801f6f2d48308d718d121f900ed44d0d3ffd31ff404f404d33fd315d1f82321a15220b98e12336df82324aa00a112b9926d32de58f82301de541675f910f2a106d0d31fd4d307d30cd309d33fd315d15168baf2a2515abaf2a6f8232aa15250bcf2a304f823bbf2a35304800df40f6fa199d024d721d70a00f2649130e20e01fe5309800df40f6fa18e13d05004d718d20001f264c858cf16cf8301cf168e1030c824cf40cf8384095005a1a514cf40e2f800c94039800df41704c8cbff13cb1ff40012f40012cb3f12cb15c9ed54f80f21d0d30001f265d3020171b0925f03e0fa4001d70b01c000f2a5fa4031fa0031f401fa0031fa00318060d721d300010f0020f265d2000193d431d19130e272b1fb00b585bf03")
if err != nil {
  log.Fatal(err)
}

HIGHLOAD_V3_CODE, err := cell.FromBOC(codeb)
if err != nil {
  log.Fatal(err)
}
```

</TabItem>
<TabItem value="python" label="Python">

```python
from pytoniq import Cell

HIGHLOAD_V3_CODE = Cell.one_from_boc("b5ee9c7241021001000228000114ff00f4a413f4bcf2c80b01020120020d02014803040078d020d74bc00101c060b0915be101d0d3030171b0915be0fa4030f828c705b39130e0d31f018210ae42e5a4ba9d8040d721d74cf82a01ed55fb04e030020120050a02027306070011adce76a2686b85ffc00201200809001aabb6ed44d0810122d721d70b3f0018aa3bed44d08307d721d70b1f0201200b0c001bb9a6eed44d0810162d721d70b15800e5b8bf2eda2edfb21ab09028409b0ed44d0810120d721f404f404d33fd315d1058e1bf82325a15210b99f326df82305aa0015a112b992306dde923033e2923033e25230800df40f6fa19ed021d721d70a00955f037fdb31e09130e259800df40f6fa19cd001d721d70a00937fdb31e0915be270801f6f2d48308d718d121f900ed44d0d3ffd31ff404f404d33fd315d1f82321a15220b98e12336df82324aa00a112b9926d32de58f82301de541675f910f2a106d0d31fd4d307d30cd309d33fd315d15168baf2a2515abaf2a6f8232aa15250bcf2a304f823bbf2a35304800df40f6fa199d024d721d70a00f2649130e20e01fe5309800df40f6fa18e13d05004d718d20001f264c858cf16cf8301cf168e1030c824cf40cf8384095005a1a514cf40e2f800c94039800df41704c8cbff13cb1ff40012f40012cb3f12cb15c9ed54f80f21d0d30001f265d3020171b0925f03e0fa4001d70b01c000f2a5fa4031fa0031f401fa0031fa00318060d721d300010f0020f265d2000193d431d19130e272b1fb00b585bf03")
```

</TabItem>
</Tabs> 

Unlike the other examples, here we will work [with a ready-made wrapper](https://github.com/aSpite/highload-wallet-contract-v3/blob/main/wrappers/HighloadWalletV3.ts), as it will be quite difficult and time-consuming to build each message manually. To create an instance of the HighloadWalletV3 class, we pass `publicKey`, `subwalletId` and `timeout` and also the code:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { TonClient } from "@ton/ton";
import { HighloadWalletV3 } from "./wrappers/HighloadWalletV3"; 
import { mnemonicToWalletKey } from "@ton/crypto";

const client = new TonClient({
    endpoint: 'https://toncenter.com/api/v2/jsonRPC',
    apiKey: 'put your api key' // you can get an api key from @tonapibot bot in Telegram
});

const walletMnemonicArray = 'put your mnemonic'.split(' ');
const walletKeyPair = await mnemonicToWalletKey(walletMnemonicArray); // extract private and public keys from mnemonic
const wallet = client.open(HighloadWalletV3.createFromConfig({
    publicKey: walletKeyPair.publicKey,
    subwalletId: 0x10ad,
    timeout: 60 * 60, // 1 hour
}, HIGHLOAD_V3_CODE));

console.log(`Wallet address: ${wallet.address.toString()}`);
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
	"context"
	"crypto/ed25519"
	"log"
	"strings"

	"github.com/xssnick/tonutils-go/liteclient"
	"github.com/xssnick/tonutils-go/ton"
	"github.com/xssnick/tonutils-go/ton/wallet"
	"github.com/xssnick/tonutils-go/tvm/cell"
)

client := liteclient.NewConnectionPool()

// connect to testnet lite server
configUrl := "https://ton-blockchain.github.io/testnet-global.config.json"
err := client.AddConnectionsFromConfigUrl(context.Background(), configUrl)
if err != nil {
  panic(err)
}

api := ton.NewAPIClient(client, ton.ProofCheckPolicyFast).WithRetry()

// seed words of existed account
words := strings.Split("put your mnemonic", " ")

// choose your wallet version
w, err := wallet.FromSeed(api, words, wallet.V4R2) 
if err != nil {
  log.Fatalln("FromSeed err:", err.Error())
  return
}

timeout := 60 * 60

data := cell.BeginCell().
  MustStoreSlice(w.PrivateKey().Public().(ed25519.PublicKey), 256).
  MustStoreUInt(uint64(w.GetSubwalletID()), 32).
  MustStoreUInt(0, 66).
  MustStoreUInt(uint64(timeout), 22).
  EndCell()
```

</TabItem>
<TabItem value="python" label="Python">

```python
from pytoniq import LiteClient, WalletV4
import asyncio

async def main():
    client = LiteClient.from_testnet_config(
        ls_i=0,  # index of liteserver from config
        trust_level=2,  # trust level to liteserver
        timeout=15  # timeout not includes key blocks synchronization as it works in pytonlib
    )

    await client.connect()

    wallet: WalletV4 = await WalletV4.from_mnemonic(client, "put your mnemonic", version="v4r2") # choose your wallet version
    print(wallet.address.to_str())
    print(wallet.balance)

asyncio.run(main())
```

</TabItem>
</Tabs> 

Now we need a regular wallet, from which we will deploy the contract (we created regular wallets for GO and Python on the previous step):

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { WalletContractV3R2 } from "@ton/ton";

const deployerWalletMnemonicArray = 'put your mnemonic'.split(' ');
const deployerWalletKeyPair = await mnemonicToWalletKey(deployerWalletMnemonicArray); // extract private and public keys from mnemonic
const deployerWallet = client.open(WalletContractV3R2.create({
    publicKey: deployerWalletKeyPair.publicKey,
    workchain: 0
}));
console.log(`Deployer wallet address: ${deployerWallet.address.toString()}`);
```

</TabItem>
</Tabs> 

If you have a V4 version wallet, you can use the `WalletContractV4` class. Now, all we have to do is to deploy the contract:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
await wallet.sendDeploy(deployerWallet.sender(deployerWalletKeyPair.secretKey), toNano(0.05));
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
	"context"
	"log"

	"github.com/xssnick/tonutils-go/tlb"
	"github.com/xssnick/tonutils-go/ton/wallet"
)

comment, err := wallet.CreateCommentCell("deploy HighLoaad V3!")
if err != nil {
  log.Fatal(err)
}

addr, _, _, err := w.DeployContractWaitTransaction(context.Background(), tlb.MustFromTON("0.02"), comment, HIGHLOAD_V3_CODE, data)
if err != nil {
  log.Fatalln("Deploy HighLoaad V3 err:", err.Error())
  return
}
log.Printf("contract address: %s\n", addr.String())
```

</TabItem>
<TabItem value="python" label="Pyhton">

```python
from pytoniq import begin_cell, StateInit, Address, Cell, WalletV4
import asyncio

async def main():
  comment: Cell = begin_cell().store_uint(0, 32).store_string("Hello from python!").end_cell()    
  state_init : StateInit = StateInit(code=HIGHLOAD_V3_CODE, data=data)
  wc = 0
  dest = Address((wc, state_init.serialize().hash))
  await wallet.transfer(destination=dest, state_init=state_init, body=comment, amount=20000000)

asyncio.run(main())
```

</TabItem>
</Tabs> 

By viewing the address that was output to the console in explorer, we can verify that our wallet is deployed.

### Sending High-Load Wallet V3 Messages

Sending messages is also done through the wrapper, but in this case we will need to additionally keep the Query ID up to date. First, let's get an instance of our wallet class:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { Address } from "@ton/core";
import { TonClient } from "@ton/ton";
import { HighloadWalletV3 } from "./wrappers/HighloadWalletV3";
import { mnemonicToWalletKey } from "@ton/crypto";

const client = new TonClient({
    endpoint: 'https://toncenter.com/api/v2/jsonRPC',
    apiKey: 'put your api key' // you can get an api key from @tonapibot bot in Telegram
});

const walletMnemonicArray = 'put your mnemonic'.split(' ');
const walletKeyPair = await mnemonicToWalletKey(walletMnemonicArray); // extract private and public keys from mnemonic
const wallet = client.open(HighloadWalletV3.createFromAddress(Address.parse('put your high-load wallet address')));
console.log(`Wallet address: ${wallet.address.toString()}`);
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
	"context"
	"encoding/base64"
	"log"
	"strings"
	"time"

	"github.com/xssnick/tonutils-go/address"
	"github.com/xssnick/tonutils-go/liteclient"
	"github.com/xssnick/tonutils-go/tlb"
	"github.com/xssnick/tonutils-go/ton"
	"github.com/xssnick/tonutils-go/ton/wallet"
)

client := liteclient.NewConnectionPool()

// connect to testnet lite server
configUrl := "https://ton-blockchain.github.io/testnet-global.config.json"
err := client.AddConnectionsFromConfigUrl(context.Background(), configUrl)
if err != nil {
  panic(err)
}

api := ton.NewAPIClient(client, ton.ProofCheckPolicyFast).WithRetry()

// seed words of account, you can generate them with any wallet or using wallet.NewSeed() method
words := strings.Split("put your api key", " ")

// initialize high-load wallet
w, err := wallet.FromSeed(api, words, wallet.ConfigHighloadV3{
  MessageTTL: 60 * 5,
  MessageBuilder: func(ctx context.Context, subWalletId uint32) (id uint32, createdAt int64, err error) {
    // Due to specific of externals emulation on liteserver,
    // we need to take something less than or equals to block time, as message creation time,
    // otherwise external message will be rejected, because time will be > than emulation time
    // hope it will be fixed in the next LS versions
    createdAt = time.Now().Unix() - 30

    // example query id which will allow you to send 1 tx per second
    // but you better to implement your own iterator in database, then you can send unlimited
    // but make sure id is less than 1 << 23, when it is higher start from 0 again
    return uint32(createdAt % (1 << 23)), createdAt, nil
  },
})
if err != nil {
  log.Fatalln("FromSeed err:", err.Error())
  return
}

log.Println("wallet address:", w.WalletAddress())
```

</TabItem>
<TabItem value="python" label="Python">

```python
async def main():
  # there is now native high-load wallet v3 support on python SDK, so we use v2 class as wrapper
  hightwallet: HighloadWallet = await HighloadWallet.from_state_init(client, workchain=0, state_init=state_init, private_key=wallet.private_key)
  print(hightwallet.address.to_str())
  print(hightwallet.balance)

asyncio.run(main())
```

</TabItem>
</Tabs> 

Next several steps are for JavaScript only. Now we need to create an instance of the `HighloadQueryId` class. This class makes it easy to work with `shift` and `bit_number`. To create it, we use the `fromShiftAndBitNumber` method:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { HighloadQueryId } from "./wrappers/HighloadQueryId";

const queryHandler = HighloadQueryId.fromShiftAndBitNumber(0n, 0n);
```

</TabItem>
</Tabs> 

We put zeros here since this is the first request. However, if you've sent any messages before, you'll need to pick an unused combination of these values. Now let's create an array where we will store all our actions and add one action to it to get our TONs back:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { beginCell, internal, OutActionSendMsg, SendMode, toNano } from "@ton/core";

const actions: OutActionSendMsg[] = [];
actions.push({
    type: 'sendMsg',
    mode: SendMode.CARRY_ALL_REMAINING_BALANCE,
    outMsg: internal({
        to: Address.parse('put address of deployer wallet'),
        value: toNano(0),
        body: beginCell()
            .storeUint(0, 32)
            .storeStringTail('Hello, TON!')
            .endCell()
    })
});
```

</TabItem>
</Tabs> 

Next we just need to fill in the `subwalletId`, `timeout`, `internalMessageValue` and `createdAt` fields to send the message:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
const subwalletId = 0x10ad;
const timeout = 60 * 60; // must be same as in the contract
const internalMessageValue = toNano(0.01); // in real case it is recommended to set the value to 1 TON
const createdAt = Math.floor(Date.now() / 1000) - 60; // LiteServers have some delay in time
await wallet.sendBatch(
    walletKeyPair.secretKey,
    actions,
    subwalletId,
    queryHandler,
    timeout,
    internalMessageValue,
    SendMode.PAY_GAS_SEPARATELY,
    createdAt
);
```

</TabItem>
</Tabs> 

After submitting, we should use the `getNext` method in `queryHandler` and save the current value. In a real case, this value should be stored in the database and reset after the `timeout * 2` time.

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
queryHandler.getNext();
```

</TabItem>
</Tabs> 

Folow several steps to send multiple messages via GO/Python:

<Tabs groupId="code-examples">
<TabItem value="go" label="Golang">

```go
// source to create messages from
var receivers = map[string]string{
  "EQCD39VS5jcptHL8vMjEXrzGaRcCVYto7HUn4bpAOg8xqB2N": "0.001",
  "EQBx6tZZWa2Tbv6BvgcvegoOQxkRrVaBVwBOoW85nbP37_Go": "0.002",
  "EQBLS8WneoKVGrwq2MO786J6ruQNiv62NXr8Ko_l5Ttondoc": "0.003",
}

// create comment cell to send in body of each message (optional)
comment, err := wallet.CreateCommentCell("Hello from Highload Wallet!")
if err != nil {
  log.Fatalln("CreateComment err:", err.Error())
  return
}

var messages []*wallet.Message
// generate message for each destination, in single batch can be sent up to 65k messages (but consider messages size, external size limit is 64kb)
for addrStr, amtStr := range receivers {
  addr := address.MustParseAddr(addrStr)
  messages = append(messages, &wallet.Message{
    Mode: wallet.PayGasSeparately + wallet.IgnoreErrors, // pay fee separately, ignore action errors
    InternalMessage: &tlb.InternalMessage{
      IHRDisabled: true, // disable hyper routing (currently not works in ton)
      Bounce:      addr.IsBounceable(),
      DstAddr:     addr,
      Amount:      tlb.MustFromTON(amtStr),
      Body:        comment,
    },
  })
}

log.Println("sending transaction and waiting for confirmation...")

// send transaction that contains all our messages, and wait for confirmation
txHash, err := w.SendManyWaitTxHash(context.Background(), messages)
if err != nil {
  log.Fatalln("Transfer err:", err.Error())
  return
}

log.Println("transaction sent, hash:", base64.StdEncoding.EncodeToString(txHash))
log.Println("explorer link: https://testnet.tonscan.org/tx/" + base64.URLEncoding.EncodeToString(txHash))
```

Full example could be found [here](https://github.com/xssnick/tonutils-go/blob/master/example/highload-wallet/main.go).

</TabItem>
<TabItem value="python" label="Python">

```python
from pytoniq import begin_cell, Cell, WalletV4, HighloadWallet, LiteClient, StateInit, Address, WalletMessage
from pytoniq_core.crypto.signature import sign_message
import asyncio
import typing
import time

def pack_actions(amounts: typing.List[int], messages: typing.List[WalletMessage], dest: Address, queryId: int):
    if len(messages) > 253:
        raise Exception("messages len must be <= 253")
    
    amt = 0
    list = begin_cell().end_cell()
    mode = 3
    for i in range(len(messages)):
        amt += amounts[i]
        out_msg = messages[i].message.serialize()
        msg = begin_cell().store_uint(0x0ec3c86d, 32).store_uint(mode, 8).store_ref(out_msg)
        list = begin_cell().store_ref(list).store_cell(msg).end_cell()
    
    fees = 7000000 * len(messages) + 10000000
    amt += fees

    body = begin_cell().store_uint(0xae42e5a4, 32).store_uint(queryId, 64).store_ref(list).end_cell()
    return HighloadWallet.create_wallet_internal_message(destination=dest, value=amt, body=body)

def raw_create_transfer_msg(private_key: bytes, amounts: typing.List[int], messages: typing.List[WalletMessage], dest: Address, wallet_id: int) -> Cell:
    created_at =  int(time.time()) - 30
    queryId = created_at % (1 << 23)
    ttl = 60 * 60 # choose your ttl
    msg = pack_actions(amounts, messages, dest, queryId)
    msg_cell = msg.message.serialize()
    signing_message = begin_cell()\
        .store_uint(wallet_id, 32)\
        .store_ref(msg_cell)\
        .store_uint(msg.send_mode, 8)\
        .store_uint(queryId, 23)\
        .store_uint(created_at, 64).\
        store_uint(ttl, 22).end_cell()
    signature = sign_message(signing_message.hash, private_key)
    return begin_cell()\
        .store_bytes(signature) \
        .store_ref(signing_message) \
        .end_cell()

async def main():
    comment1: Cell = begin_cell().store_uint(0, 32).store_string("from hw1").end_cell()
    comment2: Cell = begin_cell().store_uint(0, 32).store_string("from hw2").end_cell()

    destinations=["insert destination address1", "insert destination address2"]
    bodies=[comment1, comment2]
    amounts=[1000000, 2000000] # example values
    result_msgs = []
    for i in range(len(destinations)):
        destination = destinations[i]
        body = bodies[i] if bodies[i] is not None else Cell.empty()

        if isinstance(destination, str):
            destination = Address(destination)
        result_msgs.append(HighloadWallet.create_wallet_internal_message(destination=destination, value=amounts[i], body=body))
    
    msg = raw_create_transfer_msg(private_key=wallet.private_key, amounts=amounts, messages=result_msgs, dest=dest, wallet_id=wallet.wallet_id)
    res = await hightwallet.send_external(body=msg)

asyncio.run(main())

```

</TabItem>
</Tabs> 

## 🔥 High-Load Wallet V2 (Outdated)

In some situations, sending a large number of messages per transaction may be necessary. As previously mentioned, ordinary wallets support sending up to 4 messages at a time by storing [a maximum of 4 references](/develop/data-formats/cell-boc#cell) in a single cell. High-load wallets only allow 255 messages to be sent at once. This restriction exists because the maximum number of outgoing messages (actions) in the blockchain’s config settings is set to 255.

Exchanges are probably the best example of where high-load wallets are used on a large scale. Established exchanges like Binance and others have extremely large user bases, this means that a large number of withdrawals messages are processed in short time periods. High-load wallets help address these withdrawal requests.

### High-load wallet FunC code

First, let’s examine [the code structure of high-load wallet smart contract](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/highload-wallet-v2-code.fc): 

```func
() recv_external(slice in_msg) impure {
  var signature = in_msg~load_bits(512); ;; get signature from the message body
  var cs = in_msg;
  var (subwallet_id, query_id) = (cs~load_uint(32), cs~load_uint(64)); ;; get rest values from the message body
  var bound = (now() << 32); ;; bitwise left shift operation
  throw_if(35, query_id < bound); ;; throw an error if message has expired
  var ds = get_data().begin_parse();
  var (stored_subwallet, last_cleaned, public_key, old_queries) = (ds~load_uint(32), ds~load_uint(64), ds~load_uint(256), ds~load_dict()); ;; read values from storage
  ds.end_parse(); ;; make sure we do not have anything in ds
  (_, var found?) = old_queries.udict_get?(64, query_id); ;; check if we have already had such a request
  throw_if(32, found?); ;; if yes throw an error
  throw_unless(34, subwallet_id == stored_subwallet);
  throw_unless(35, check_signature(slice_hash(in_msg), signature, public_key));
  var dict = cs~load_dict(); ;; get dictionary with messages
  cs.end_parse(); ;; make sure we do not have anything in cs
  accept_message();
```

> 💡 Useful links:
>
> ["Bitwise operations" in docs](/develop/func/stdlib/#dict_get)
>
> ["load_dict()" in docs](/develop/func/stdlib/#load_dict)
>
> ["udict_get?()" in docs](/develop/func/stdlib/#dict_get)

You notice some differences from ordinary wallets. Now let’s take a closer look at more details of how high-load wallets work on TON (except subwallets as we have gone over this previously).

### Using a Query ID In Place Of a Seqno

As we previously discussed, ordinary wallet seqno increase by `1` after each transaction. While using a wallet sequence we had to wait until this value was updated, then retrieve it using the GET method and send a new message.
This process takes a significant amount of time which high-load wallets are not designed for (as discussed above, they are meant to send a large number of messages very quickly). Therefore, high-load wallets on TON make use of the `query_id`.

If the same message request already exists, the contract won’t accept it, as it has already been processed:

```func
var (stored_subwallet, last_cleaned, public_key, old_queries) = (ds~load_uint(32), ds~load_uint(64), ds~load_uint(256), ds~load_dict()); ;; read values from storage
ds.end_parse(); ;; make sure we do not have anything in ds
(_, var found?) = old_queries.udict_get?(64, query_id); ;; check if we have already had such a request
throw_if(32, found?); ;; if yes throw an error
```

This way, we are **being protected from repeat messages**, which was the role of seqno in ordinary wallets.

### Sending Messages

After the contract has accepted the external message, a loop starts, in which the `slices` stored in the dictionary are taken. These slices store messages' modes and the messages themselves. Sending new messages takes place until the dictionary is empty.

```func
int i = -1; ;; we write -1 because it will be the smallest value among all dictionary keys
do {
  (i, var cs, var f) = dict.idict_get_next?(16, i); ;; get the key and its corresponding value with the smallest key, which is greater than i
  if (f) { ;; check if any value was found
    var mode = cs~load_uint(8); ;; load message mode
    send_raw_message(cs~load_ref(), mode); ;; load message itself and send it
  }
} until (~ f); ;; if any value was found continue
```

> 💡 Useful link:
>
> ["idict_get_next()" in docs](/develop/func/stdlib/#dict_get_next)

Note that if a value is found, `f` is always equal to -1 (true). The `~ -1` operation (bitwise not) will always return a value of 0, meaning that the loop should be continued. At the same time, when a dictionary is filled with messages, it is necessary to start calculating those **with a value greater than -1** (e.g., 0) and continue increasing the value by 1 with each message. This structure allows messages to be sent in the correct sequential order.

### Removing Expired Queries

Typically, [smart contracts on TON pay for their own storage](/develop/howto/fees-low-level#storage-fee). This means that the amount of data smart contracts can store is limited to prevent high network loading. To allow the system to be more efficient, messages that are more than 64 seconds old are removed from the storage. This is conducted as follows:


```func
bound -= (64 << 32);   ;; clean up records that have expired more than 64 seconds ago
old_queries~udict_set_builder(64, query_id, begin_cell()); ;; add current query to dictionary
var queries = old_queries; ;; copy dictionary to another variable
do {
  var (old_queries', i, _, f) = old_queries.udict_delete_get_min(64);
  f~touch();
  if (f) { ;; check if any value was found
    f = (i < bound); ;; check if more than 64 seconds have elapsed after expiration
  }
  if (f) { 
    old_queries = old_queries'; ;; if yes save changes in our dictionary
    last_cleaned = i; ;; save last removed query
  }
} until (~ f);
```

> 💡 Useful link:
>
> ["udict_delete_get_min()" in docs](/develop/func/stdlib/#dict_delete_get_min)

Note that it is necessary to interact with the `f` variable several times. Since the [TVM is a stack machine](/learn/tvm-instructions/tvm-overview#tvm-is-a-stack-machine), during each interaction with the `f` variable it is necessary to pop all values to get the desired variable. The `f~touch()` operation places the f  variable at the top of the stack to optimize code execution.

### Bitwise Operations

This section may seem a bit complicated for those who have not previously worked with bitwise operations. The following line of code can be seen in the smart contract code:

```func
var bound = (now() << 32); ;; bitwise left shift operation
```
As a result 32 bits are added to the number on the right side. This means that **existing values are moved 32 bits to the left**. For example, let’s consider the number 3 and translate it into a binary form with a result of 11. Applying the `3 << 2` operation, 11 is moved 2 bit places. This means that two bits are added to the right of the string. In the end, we have 1100, which is 12.

The first thing to understand about this process is to remember that the `now()` function returns a result of uint32, meaning that the resulting value will be 32 bits. By shifting 32 bits to the left, space is opened up for another uint32, resulting in the correct query_id. This way, the **timestamp and query_id can be combined** within one variable for optimization.

Next, let’s consider the following line of code:

```func
bound -= (64 << 32); ;; clean up the records that have expired more than 64 seconds ago
```

Above we performed an operation to shift the number 64 by 32 bits to **subtract 64 seconds** from our timestamp. This way we'll be able to compare past query_ids and see if they are less than the received value. If so, they expired more than 64 seconds ago:

```func
if (f) { ;; check if any value has been found
  f = (i < bound); ;; check if more than 64 seconds have elapsed after expiration
}
```
To understand this better, let’s use the number `1625918400` as an example of a timestamp. Its binary representation (with the left-handed addition of zeros for 32 bits) is 01100000111010011000101111000000. By performing a 32 bit bitwise left shift, the result is 32 zeros at the end of the binary representation of our number.

After this is completed, **it is possible to add any query_id (uint32)**. Then by subtracting `64 << 32` the result is a timestamp that 64 seconds ago had the same query_id. This fact can be verified by performing the following calculations `((1625918400 << 32) - (64 << 32)) >> 32`. This way we can compare the necessary portions of our number (the timestamp) and at the same time the query_id does not interfere.

### Storage Updates

After all operations are complete, the only task remaining is to save the new values in the storage:

```func
  set_data(begin_cell()
    .store_uint(stored_subwallet, 32)
    .store_uint(last_cleaned, 64)
    .store_uint(public_key, 256)
    .store_dict(old_queries)
    .end_cell());
}
```

### GET Methods

The last thing we have to consider before we dive into wallet deployment and message creation is high-load wallet GET methods:

Method | Explanation
:---: | :---:
int processed?(int query_id) | Notifies the user if a particular request has been processed. This means it returns `-1` if the request has been processed and `0` if it has not. Also, this method may return `1` if the answer is unknown since the request is old and no longer stored in the contract.
int get_public_key() | Rerive a public key. We have considered this method before.

Let’s look at the `int processed?(int query_id)` method closely to help us to understand why we need to make use of the last_cleaned:

```func
int processed?(int query_id) method_id {
  var ds = get_data().begin_parse();
  var (_, last_cleaned, _, old_queries) = (ds~load_uint(32), ds~load_uint(64), ds~load_uint(256), ds~load_dict());
  ds.end_parse();
  (_, var found) = old_queries.udict_get?(64, query_id);
  return found ? true : - (query_id <= last_cleaned);
}
```
The `last_cleaned` is retrieved from the storage of the contract and a dictionary of old queries. If the query is found, it is to be returned true, and if not, the expression `- (query_id <= last_cleaned)`. The last_cleaned contains the last removed request **with the highest timestamp**, as we started with the minimum timestamp when deleting the requests.

This means that if the query_id passed to the method is smaller than the last last_cleaned value, it is impossible to determine whether it was ever in the contract or not. Therefore the `query_id <= last_cleaned` returns -1 while the minus before this expression changes the answer to 1. If query_id is larger than last_cleaned method, then it has not yet been processed.

### Deploying High-Load Wallet V2

In order to deploy a high-load wallet it is necessary to generate a mnemonic key in advance, which will be used by the user. It is possible to use the same key that was used in previous sections of this tutorial.

To begin the process required to deploy a high-load wallet it's necessary to copy [the code of the smart contract](https://github.com/ton-blockchain/ton/blob/master/crypto/smartcont/highload-wallet-v2-code.fc) to the same directory where the stdlib.fc and wallet_v3 are located and remember to add `#include "stdlib.fc";` to the beginning of the code. Next we’ll compile the high-load wallet code like we did in [section three](/develop/smart-contracts/tutorials/wallet#compiling-wallet-code):

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { compileFunc } from '@ton-community/func-js';
import fs from 'fs'
import { Cell } from '@ton/core';

const result = await compileFunc({
    targets: ['highload_wallet.fc'], // targets of your project
    sources: {
        'stdlib.fc': fs.readFileSync('./src/stdlib.fc', { encoding: 'utf-8' }),
        'highload_wallet.fc': fs.readFileSync('./src/highload_wallet.fc', { encoding: 'utf-8' }),
    }
});

if (result.status === 'error') {
console.error(result.message)
return;
}

const codeCell = Cell.fromBoc(Buffer.from(result.codeBoc, 'base64'))[0];

// now we have base64 encoded BOC with compiled code in result.codeBoc
console.log('Code BOC: ' + result.codeBoc);
console.log('\nHash: ' + codeCell.hash().toString('base64')); // get the hash of cell and convert in to base64 encoded string

```

</TabItem>
</Tabs>

The result will be the following output in the terminal:

```text
Code BOC: te6ccgEBCQEA5QABFP8A9KQT9LzyyAsBAgEgAgMCAUgEBQHq8oMI1xgg0x/TP/gjqh9TILnyY+1E0NMf0z/T//QE0VNggED0Dm+hMfJgUXO68qIH+QFUEIf5EPKjAvQE0fgAf44WIYAQ9HhvpSCYAtMH1DAB+wCRMuIBs+ZbgyWhyEA0gED0Q4rmMQHIyx8Tyz/L//QAye1UCAAE0DACASAGBwAXvZznaiaGmvmOuF/8AEG+X5dqJoaY+Y6Z/p/5j6AmipEEAgegc30JjJLb/JXdHxQANCCAQPSWb6VsEiCUMFMDud4gkzM2AZJsIeKz

Hash: lJTRzI7fEvBWcaGpugmSEJbrUIEeGSTsZcPGKfu4CBI=
```

With the above result it is possible to use the base64 encoded output to retrieve the cell with our wallet code in other libraries and languages as follows:

<Tabs groupId="code-examples">
<TabItem value="go" label="Golang">

```go
import (
  "encoding/base64"
  "github.com/xssnick/tonutils-go/tvm/cell"
  "log"
)

base64BOC := "te6ccgEBCQEA5QABFP8A9KQT9LzyyAsBAgEgAgMCAUgEBQHq8oMI1xgg0x/TP/gjqh9TILnyY+1E0NMf0z/T//QE0VNggED0Dm+hMfJgUXO68qIH+QFUEIf5EPKjAvQE0fgAf44WIYAQ9HhvpSCYAtMH1DAB+wCRMuIBs+ZbgyWhyEA0gED0Q4rmMQHIyx8Tyz/L//QAye1UCAAE0DACASAGBwAXvZznaiaGmvmOuF/8AEG+X5dqJoaY+Y6Z/p/5j6AmipEEAgegc30JjJLb/JXdHxQANCCAQPSWb6VsEiCUMFMDud4gkzM2AZJsIeKz" // save our base64 encoded output from compiler to variable
codeCellBytes, _ := base64.StdEncoding.DecodeString(base64BOC) // decode base64 in order to get byte array
codeCell, err := cell.FromBOC(codeCellBytes) // get cell with code from byte array
if err != nil { // check if there is any error
  panic(err) 
}

log.Println("Hash:", base64.StdEncoding.EncodeToString(codeCell.Hash())) // get the hash of our cell, encode it to base64 because it has []byte type and output to the terminal
```

</TabItem>
</Tabs>

Now we need to retrieve a cell composed of its initial data, build a State Init, and calculate a high-load wallet address. After studying the smart contract code it became clear that the subwallet_id, last_cleaned, public_key and old_queries are sequentially stored in the storage:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { Address, beginCell } from '@ton/core';
import { mnemonicToWalletKey } from '@ton/crypto';

const highloadMnemonicArray = 'put your mnemonic that you have generated and saved before'.split(' ');
const highloadKeyPair = await mnemonicToWalletKey(highloadMnemonicArray); // extract private and public keys from mnemonic

const dataCell = beginCell()
    .storeUint(698983191, 32) // Subwallet ID
    .storeUint(0, 64) // Last cleaned
    .storeBuffer(highloadKeyPair.publicKey) // Public Key
    .storeBit(0) // indicate that the dictionary is empty
    .endCell();

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
  "crypto/ed25519"
  "crypto/hmac"
  "crypto/sha512"
  "github.com/xssnick/tonutils-go/address"
  "golang.org/x/crypto/pbkdf2"
  "strings"
)

highloadMnemonicArray := strings.Split("put your mnemonic that you have generated and saved before", " ") // word1 word2 word3
mac := hmac.New(sha512.New, []byte(strings.Join(highloadMnemonicArray, " ")))
hash := mac.Sum(nil)
k := pbkdf2.Key(hash, []byte("TON default seed"), 100000, 32, sha512.New) // In TON libraries "TON default seed" is used as salt when getting keys
// 32 is a key len
highloadPrivateKey := ed25519.NewKeyFromSeed(k)                      // get private key
highloadPublicKey := highloadPrivateKey.Public().(ed25519.PublicKey) // get public key from private key

dataCell := cell.BeginCell().
  MustStoreUInt(698983191, 32).           // Subwallet ID
  MustStoreUInt(0, 64).                   // Last cleaned
  MustStoreSlice(highloadPublicKey, 256). // Public Key
  MustStoreBoolBit(false).                // indicate that the dictionary is empty
  EndCell()

stateInit := cell.BeginCell().
  MustStoreBoolBit(false). // No split_depth
  MustStoreBoolBit(false). // No special
  MustStoreBoolBit(true).  // We have code
  MustStoreRef(codeCell).
  MustStoreBoolBit(true). // We have data
  MustStoreRef(dataCell).
  MustStoreBoolBit(false). // No library
  EndCell()

contractAddress := address.NewAddress(0, 0, stateInit.Hash()) // get the hash of stateInit to get the address of our smart contract in workchain with ID 0
log.Println("Contract address:", contractAddress.String())    // Output contract address to console
```

</TabItem>
</Tabs> 

:::caution
Everything we have detailed above follows the same steps as the contract [deployment via wallet](/develop/smart-contracts/tutorials/wallet#contract-deployment-via-wallet) section. To better understanding, read the entire [GitHub source code]((https://github.com/aSpite/wallet-tutorial)).
:::

### Sending High-Load Wallet V2 Messages

Now let’s program a high-load wallet to send several messages at the same time. For example, let's take 12 messages per transaction so that the gas fees are small. 

:::info High-load balance
To complete the transaction, the balance of the contract must be at least 0.5 TON.
:::

Each message carry its own comment with code and the destination address will be the wallet from which we deployed:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { Address, beginCell, Cell, toNano } from '@ton/core';

let internalMessages:Cell[] = [];
const walletAddress = Address.parse('put your wallet address from which you deployed high-load wallet');

for (let i = 0; i < 12; i++) {
    const internalMessageBody = beginCell()
        .storeUint(0, 32)
        .storeStringTail(`Hello, TON! #${i}`)
        .endCell();

    const internalMessage = beginCell()
        .storeUint(0x18, 6) // bounce
        .storeAddress(walletAddress)
        .storeCoins(toNano('0.01'))
        .storeUint(0, 1 + 4 + 4 + 64 + 32)
        .storeBit(0) // We do not have State Init
        .storeBit(1) // We store Message Body as a reference
        .storeRef(internalMessageBody) // Store Message Body Init as a reference
        .endCell();

    internalMessages.push(internalMessage);
}
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
  "fmt"
  "github.com/xssnick/tonutils-go/address"
  "github.com/xssnick/tonutils-go/tlb"
  "github.com/xssnick/tonutils-go/tvm/cell"
)

var internalMessages []*cell.Cell
walletAddress := address.MustParseAddr("put your wallet address from which you deployed high-load wallet")

for i := 0; i < 12; i++ {
  comment := fmt.Sprintf("Hello, TON! #%d", i)
  internalMessageBody := cell.BeginCell().
    MustStoreUInt(0, 32).
    MustStoreBinarySnake([]byte(comment)).
    EndCell()

  internalMessage := cell.BeginCell().
    MustStoreUInt(0x18, 6). // bounce
    MustStoreAddr(walletAddress).
    MustStoreBigCoins(tlb.MustFromTON("0.001").NanoTON()).
    MustStoreUInt(0, 1+4+4+64+32).
    MustStoreBoolBit(false). // We do not have State Init
    MustStoreBoolBit(true). // We store Message Body as a reference
    MustStoreRef(internalMessageBody). // Store Message Body Init as a reference
    EndCell()

  messageData := cell.BeginCell().
    MustStoreUInt(3, 8). // transaction mode
    MustStoreRef(internalMessage).
    EndCell()

	internalMessages = append(internalMessages, messageData)
}
```

</TabItem>
</Tabs>

After completing the above process, the result is an array of internal messages. Next, it's necessary to create a dictionary for message storage and prepare and sign the message body. This is completed as follows:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { Dictionary } from '@ton/core';
import { mnemonicToWalletKey, sign } from '@ton/crypto';
import * as crypto from 'crypto';

const dictionary = Dictionary.empty<number, Cell>(); // create an empty dictionary with the key as a number and the value as a cell
for (let i = 0; i < internalMessages.length; i++) {
    const internalMessage = internalMessages[i]; // get our message from an array
    dictionary.set(i, internalMessage); // save the message in the dictionary
}

const queryID = crypto.randomBytes(4).readUint32BE(); // create a random uint32 number, 4 bytes = 32 bits
const now = Math.floor(Date.now() / 1000); // get current timestamp
const timeout = 120; // timeout for message expiration, 120 seconds = 2 minutes
const finalQueryID = (BigInt(now + timeout) << 32n) + BigInt(queryID); // get our final query_id
console.log(finalQueryID); // print query_id. With this query_id we can call GET method to check if our request has been processed

const toSign = beginCell()
    .storeUint(698983191, 32) // subwallet_id
    .storeUint(finalQueryID, 64)
    // Here we create our own method that will save the 
    // message mode and a reference to the message
    .storeDict(dictionary, Dictionary.Keys.Int(16), {
        serialize: (src, buidler) => {
            buidler.storeUint(3, 8); // save message mode, mode = 3
            buidler.storeRef(src); // save message as reference
        },
        // We won't actually use this, but this method 
        // will help to read our dictionary that we saved
        parse: (src) => {
            let cell = beginCell()
                .storeUint(src.loadUint(8), 8)
                .storeRef(src.loadRef())
                .endCell();
            return cell;
        }
    }
);

const highloadMnemonicArray = 'put your high-load wallet mnemonic'.split(' ');
const highloadKeyPair = await mnemonicToWalletKey(highloadMnemonicArray); // extract private and public keys from mnemonic
const highloadWalletAddress = Address.parse('put your high-load wallet address');

const signature = sign(toSign.endCell().hash(), highloadKeyPair.secretKey); // get the hash of our message to wallet smart contract and sign it to get signature
```

</TabItem>
<TabItem value="go" label="Golang">

```go
import (
  "crypto/ed25519"
  "crypto/hmac"
  "crypto/sha512"
  "golang.org/x/crypto/pbkdf2"
  "log"
  "math/big"
  "math/rand"
  "strings"
  "time"
)

dictionary := cell.NewDict(16) // create an empty dictionary with the key as a number and the value as a cell
for i := 0; i < len(internalMessages); i++ {
  internalMessage := internalMessages[i]                             // get our message from an array
  err := dictionary.SetIntKey(big.NewInt(int64(i)), internalMessage) // save the message in the dictionary
  if err != nil {
    return
  }
}

queryID := rand.Uint32()
timeout := 120                                                               // timeout for message expiration, 120 seconds = 2 minutes
now := time.Now().Add(time.Duration(timeout)*time.Second).UTC().Unix() << 32 // get current timestamp + timeout
finalQueryID := uint64(now) + uint64(queryID)                                // get our final query_id
log.Println(finalQueryID)                                                    // print query_id. With this query_id we can call GET method to check if our request has been processed

toSign := cell.BeginCell().
  MustStoreUInt(698983191, 32). // subwallet_id
  MustStoreUInt(finalQueryID, 64).
  MustStoreDict(dictionary)

highloadMnemonicArray := strings.Split("put your high-load wallet mnemonic", " ") // word1 word2 word3
mac := hmac.New(sha512.New, []byte(strings.Join(highloadMnemonicArray, " ")))
hash := mac.Sum(nil)
k := pbkdf2.Key(hash, []byte("TON default seed"), 100000, 32, sha512.New) // In TON libraries "TON default seed" is used as salt when getting keys
// 32 is a key len
highloadPrivateKey := ed25519.NewKeyFromSeed(k) // get private key
highloadWalletAddress := address.MustParseAddr("put your high-load wallet address")

signature := ed25519.Sign(highloadPrivateKey, toSign.EndCell().Hash())
```

</TabItem>
</Tabs>

:::note IMPORTANT
Note that while using JavaScript and TypeScript that our messages were saved into an array without using a send mode. This occurs because during using @ton/ton library, it is expected that developer will implement process of serialization and deserialization by own hands. Therefore, a method is passed that first saves the message mode after it saves the message itself. If we make use of the `Dictionary.Values.Cell()` specification for the value method, it saves the entire message as a cell reference without saving the mode separately.
:::

Next we’ll create an external message and send it to the blockchain using the following code:

<Tabs groupId="code-examples">
<TabItem value="js" label="JavaScript">

```js
import { TonClient } from '@ton/ton';

const body = beginCell()
    .storeBuffer(signature) // store signature
    .storeBuilder(toSign) // store our message
    .endCell();

const externalMessage = beginCell()
    .storeUint(0b10, 2) // indicate that it is an incoming external message
    .storeUint(0, 2) // src -> addr_none
    .storeAddress(highloadWalletAddress)
    .storeCoins(0) // Import fee
    .storeBit(0) // We do not have State Init
    .storeBit(1) // We store Message Body as a reference
    .storeRef(body) // Store Message Body as a reference
    .endCell();

// We do not need a key here as we will be sending 1 request per second
const client = new TonClient({
    endpoint: 'https://toncenter.com/api/v2/jsonRPC',
    // apiKey: 'put your api key' // you can get an api key from @tonapibot bot in Telegram
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

body := cell.BeginCell().
  MustStoreSlice(signature, 512). // store signature
  MustStoreBuilder(toSign). // store our message
  EndCell()

externalMessage := cell.BeginCell().
  MustStoreUInt(0b10, 2). // ext_in_msg_info$10
  MustStoreUInt(0, 2). // src -> addr_none
  MustStoreAddr(highloadWalletAddress). // Destination address
  MustStoreCoins(0). // Import Fee
  MustStoreBoolBit(false). // No State Init
  MustStoreBoolBit(true). // We store Message Body as a reference
  MustStoreRef(body). // Store Message Body as a reference
  EndCell()

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

After this process is completed it is possible to look up our wallet and verify that 12 outgoing messages were sent on our wallet. Is it also possible to call the `processed?` GET method using the query_id we initially used in the console. If this request has been processed correctly it provides a result of `-1` (true).