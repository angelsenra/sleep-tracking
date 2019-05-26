#! python3
import model
import utils.log
import utils.telegram

logger = utils.log.get("start")

if __name__ == "__main__":
    logger.warning("Setting webhook")
    bot = utils.telegram.Bot()
    bot.set_webhook()

    logger.warning("Creating database")
    model.main()
