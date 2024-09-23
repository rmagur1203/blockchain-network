import { BlockchainService } from '@app/blockchain';
import { Injectable } from '@nestjs/common';
import { PostTransactionsNewDto } from './dto/PostTransactionsNew.dto';
import { Blockchain } from '@blockchain/core';

@Injectable()
export class AppService {
  constructor(private readonly blockchainService: BlockchainService) {}

  getFullChain() {
    const chain = this.blockchainService.getFullChain();
    return {
      chain,
      length: chain.length,
    };
  }

  mining() {
    const lastBlock = this.blockchainService.blockchain.last_block;
    const lastProof = lastBlock.nonce;
    const proof = this.blockchainService.blockchain.pow(lastProof);

    this.blockchainService.blockchain.new_transaction('0', 'node', 1);

    const previousHash = Blockchain.hash(lastBlock);
    const block = this.blockchainService.blockchain.new_block(
      proof,
      previousHash,
    );

    return {
      message: 'New Block Forged',
      index: block.index,
      transactions: block.transactions,
      proof: block.nonce,
      previousHash: block.previous_hash,
    };
  }

  newTransaction(body: PostTransactionsNewDto) {
    const index = this.blockchainService.newTransaction(
      body.sender,
      body.recipient,
      body.amount,
    );
    return {
      message: `Transaction will be added to Block ${index}`,
    };
  }
}
