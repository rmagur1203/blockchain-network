import { Body, Controller, Get, Post } from '@nestjs/common';
import { AppService } from './app.service';
import { PostTransactionsNewDto } from './dto/PostTransactionsNew.dto';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get('chain')
  full_chain() {
    return this.appService.getFullChain();
  }

  @Get('mine')
  mine() {
    return this.appService.mining();
  }

  @Post('/transactions/new')
  new_transaction(@Body() body: PostTransactionsNewDto) {
    return this.appService.newTransaction(body);
  }
}
