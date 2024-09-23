import { Transaction } from "./transaction";

export interface Block {
  index: number;
  timestamp: Date;
  transactions: Transaction[];
  nonce: number;
  previous_hash: string;
}
