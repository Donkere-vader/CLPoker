# CL Poker


## TODO
- [X] Server
    - [X] Table
        - [X] Port
            - [X] socket.getfreeport()?
        - [X] Name
        - [ ] Chat **(NOT FOR v1.0)**
            - [ ] Receive messages **(NOT FOR v1.0)**
            - [ ] Distribute messages under players **(NOT FOR v1.0)**
        - [X] Players
        - [X] Shuffle
        - [X] check cards
        - [X] flop
        - [X] river
    - [X] New connection
    - [X] New table
- [X] Client
    - [X] Connect to server
        - [X] Connection lost message
    - [X] Connect to table
        - [X] Leave table
        - [X] Update table
    - [X] Tkinter
        - [X] Display table
        - [X] Buttons

- [ ] Finishing up
    - while bugs:
        - [ ] Bug fixxing (Busy)
        - [ ] Testing
    - [ ] build v1.0 (pyinstaller)
    - [ ] testing by friends (if bugs back to while loop)

## :bug: BUGS
 - [X] Call money doesn't get written off
 - [X] End of round bet reset
 - [X] Invalid port error messages misses a return out of the funciton
 - [X] Call to is a negative number?
 - [X] Starting game at table... red time color in console, should be green
 - [X] try except continue on TimeoutError

## Before build
 - [ ] Remove flop and river and cards print in client