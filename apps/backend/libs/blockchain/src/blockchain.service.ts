import { Injectable } from '@nestjs/common';
import { Block, Blockchain } from '@blockchain/core';

@Injectable()
export class BlockchainService {
  blockchain = new Blockchain();

  getFullChain(): Block[] {
    return this.blockchain.chain;
  }

  newTransaction(sender: string, recipient: string, amount: number): number {
    return this.blockchain.new_transaction(sender, recipient, amount);
  }
}
