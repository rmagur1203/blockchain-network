import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { BlockchainModule } from '@app/blockchain';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
    BlockchainModule,
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: [`../../../.env`, `.env`],
    }),
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
