import crypto from "crypto";
import { Block } from "./types/block";
import { Transaction } from "./types/transaction";

const DIFFICULTY = 4;

export class Blockchain {
  chain: Block[] = [];
  current_transactions: Transaction[] = [];
  nodes = new Set();

  get last_block() {
    return this.chain[this.chain.length - 1];
  }

  static hash(block: Block) {
    const block_string = JSON.stringify(block, Object.keys(block).sort());
    return crypto.createHash("sha256").update(block_string).digest("hex");
  }

  static valid_proof(last_proof: number, proof: number) {
    const guess = `${last_proof}${proof}`;
    const guess_hash = crypto.createHash("sha256").update(guess).digest("hex");
    return guess_hash.slice(0, DIFFICULTY) === "0".repeat(DIFFICULTY);
  }

  constructor() {
    this.new_block(100, "1");
  }

  pow(last_proof: number) {
    let proof = 0;
    while (!Blockchain.valid_proof(last_proof, proof)) {
      proof++;
    }
    return proof;
  }

  new_transaction(sender: string, recipient: string, amount: number) {
    this.current_transactions.push({
      sender,
      recipient,
      amount,
      timestamp: new Date(),
    });
    return this.last_block.index + 1;
  }

  new_block(proof: number, previous_hash?: string) {
    const block: Block = {
      index: this.chain.length + 1,
      timestamp: new Date(),
      transactions: this.current_transactions,
      nonce: proof,
      previous_hash: previous_hash ?? Blockchain.hash(this.last_block),
    };
    this.current_transactions = [];
    this.chain.push(block);
    return block;
  }

  valid_chain(chain: Block[]) {
    let last_block = chain[0];
    let current_index = 1;

    while (current_index < chain.length) {
      const block = chain[current_index];
      if (block.previous_hash !== Blockchain.hash(last_block)) {
        return false;
      }
      if (!Blockchain.valid_proof(last_block.nonce, block.nonce)) {
        return false;
      }
      last_block = block;
      current_index++;
    }
    return true;
  }
}
