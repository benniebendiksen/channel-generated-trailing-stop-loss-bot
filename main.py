from src.TrailingStopLossActivation import TrailingStopLossActivation

if __name__ == "__main__":
    while True:
        try:
            Tsa = TrailingStopLossActivation()
            print('exit called')
        except SystemExit as e:
            if e.code == 1:
                continue
            else:
                print("System Exited")
                break