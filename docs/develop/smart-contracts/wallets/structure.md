import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# 💎 TON Blockchain Wallets

All wallets that operate and run on TON Blockchain are actually smart contracts, in the same way, everything operating on TON is a smart contract. Like most blockchains, it is possible to deploy smart contracts on the network and customize them for different uses. Thanks to this feature, **full wallet customization is possible**.
On TON wallet smart contracts help the platform communicate with other smart contract types. However, it is important to consider how wallet communication takes place.

## Wallet Communication
Generally, there are two message types on TON Blockchain: `internal` and `external`. External messages allow for the ability to send messages to the blockchain from the outside world, thus allowing for the communication with smart contracts that accept such messages. The function responsible for carrying out this process is as follows:

```func
() recv_external(slice in_msg) impure {
    ;; some code
}
```
Before we dive into more details concerning wallets, let’s look at how wallets accept external messages. On TON, all wallets hold the owner’s `public key`, `seqno`, and `subwallet_id`. When receiving an external message, the wallet uses the `get_data()` method to retrieve data from the storage portion of the wallet. It then conducts several verification procedures and decides whether to accept the message or not. This process is conducted as follows:

```func
() recv_external(slice in_msg) impure {
  var signature = in_msg~load_bits(512); ;; get signature from the message body
  var cs = in_msg;
  var (subwallet_id, valid_until, msg_seqno) = (cs~load_uint(32), cs~load_uint(32), cs~load_uint(32));  ;; get rest values from the message body
  throw_if(35, valid_until <= now()); ;; check the relevance of the message
  var ds = get_data().begin_parse(); ;; get data from storage and convert it into a slice to be able to read values
  var (stored_seqno, stored_subwallet, public_key) = (ds~load_uint(32), ds~load_uint(32), ds~load_uint(256)); ;; read values from storage
  ds.end_parse(); ;; make sure we do not have anything in ds variable
  throw_unless(33, msg_seqno == stored_seqno);
  throw_unless(34, subwallet_id == stored_subwallet);
  throw_unless(35, check_signature(slice_hash(in_msg), signature, public_key));
  accept_message();
```

> 💡 Useful links:
>
> ["load_bits()" in docs](/develop/func/stdlib/#load_bits)
>
> ["get_data()" in docs](/develop/func/stdlib/#load_bits)
>
> ["begin_parse()" in docs](/develop/func/stdlib/#load_bits)
>
> ["end_parse()" in docs](/develop/func/stdlib/#end_parse)
>
> ["load_int()" in docs](/develop/func/stdlib/#load_int)
>
> ["load_uint()" in docs](/develop/func/stdlib/#load_int)
>
> ["check_signature()" in docs](/develop/func/stdlib/#check_signature)
>
> ["slice_hash()" in docs](/develop/func/stdlib/#slice_hash)
>
> ["accept_message()" in docs](/develop/smart-contracts/guidelines/accept)

Now let’s take a closer look.

## Replay Protection - Seqno

Message replay protection in the wallet smart contract is directly related to the message seqno (Sequence Number) which keeps track of which messages are sent in which order. It is very important that a single message is not repeated from a wallet because it throws off the integrity of the system entirely. If we further examine smart contract code within a wallet, the `seqno` is typically handled as follows:

```func
throw_unless(33, msg_seqno == stored_seqno);
```

This line of code above checks the `seqno`, which comes in the message and checks it with `seqno`, which is stored in a smart contract. The contract returns an error with `33 exit code` if they do not match. So if the sender passed invalid seqno, it means that he made some mistake in the message sequence, and the contract protects against such cases.

:::note
It's also essential to consider that external messages can be sent by anyone. This means that if you send 1 TON to someone, someone else can repeat this message. However, when the seqno increases, the previous external message becomes invalid, and no one will be able to repeat it, thus preventing the possibility of stealing your funds.
:::

## Signature

As mentioned earlier, wallet smart contracts accept external messages. However, these messages come from the outside world and that data cannot be 100% trusted. Therefore, each wallet stores the owner's public key. The smart contract uses a public key to verify the legitimacy of the message signature when receiving an external message that the owner signed with the private key. This verifies that the message is actually from the contract owner.

To carry out this process, the wallet must first obtain the signature from the incoming message which loads the public key from storage and validates the signature using the following process:

```func
var signature = in_msg~load_bits(512);
var ds = get_data().begin_parse();
var (stored_seqno, stored_subwallet, public_key) = (ds~load_uint(32), ds~load_uint(32), ds~load_uint(256));
throw_unless(35, check_signature(slice_hash(in_msg), signature, public_key));
```

And if all verification processes are completed correctly, the smart contract accepts the message and processes it:

```func
accept_message();
```

:::info accept_message()
Because the message comes from the outside world, it does not contain the Toncoin required to pay the transaction fee. When sending TON using the accept_message() function, a gas_credit (at the time of writing its value is 10,000 gas units) is applied which allows the necessary calculations to be carried out for free if the gas does not exceed the gas_credit value. After the accept_message() function is used, all the gas spent (in TON) is taken from the balance of the smart contract. More can be read about this process [here](/develop/smart-contracts/guidelines/accept).
:::

## Transaction Expiration

Another step used to check the validity of external messages is the `valid_until` field. As you can see from the variable name, this is the time in UNIX before the message is valid. If this verification process fails, the contract completes the processing of the transaction and returns the 35 exit code follows:

```func
var (subwallet_id, valid_until, msg_seqno) = (cs~load_uint(32), cs~load_uint(32), cs~load_uint(32));
throw_if(35, valid_until <= now());
```

This algorithm works to protect against the susceptibility of various errors when the message is no longer valid but was still sent to the blockchain for an unknown reason.

## Wallet v3 and Wallet v4 Differences

The only difference between Wallet v3 and Wallet v4 is that Wallet v4 makes use of `plugins` that can be installed and deleted. These plugins are special smart contracts which are able to request a specific number of TON at a specific time from a wallet smart contract.

Wallet smart contracts, in turn, will send the required amount of TON in response without the need for the owner to participate. This is similar to the **subscription model** for which plugins are created. We will not learn these details, because this is out of the scope of this tutorial.

## How Wallets facilitate communication with Smart Contracts

As we discussed earlier, a wallet smart contract accepts external messages, validates them and accepts them if all checks are passed. The contract then starts the loop of retrieving messages from the body of external messages then creates internal messages and sends them to the blockchain as follows:


```func
cs~touch();
while (cs.slice_refs()) {
    var mode = cs~load_uint(8); ;; load message mode
    send_raw_message(cs~load_ref(), mode); ;; get each new internal message as a cell with the help of load_ref() and send it
}
```

:::tip touch()
On TON, all smart contracts run on the stack-based TON Virtual Machine (TVM). ~ touch() places the variable `cs` on top of the stack to optimize the running of code for less gas.
:::

Since a **maximum of 4 references** can be stored in one cell, we can send a maximum of 4 internal messages per external message.

> 💡 Useful links:
>
> ["slice_refs()" in docs](/develop/func/stdlib/#slice_refs)
>
> ["send_raw_message() and message modes" in docs](/develop/func/stdlib/#send_raw_message)
>
> ["load_ref()" in docs](/develop/func/stdlib/#load_ref)

