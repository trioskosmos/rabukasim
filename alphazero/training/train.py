import sys

from alphazero.training.overnight_vanilla import main


if __name__ == "__main__":
    main(["train", *sys.argv[1:]])
