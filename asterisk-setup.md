# Asterisk Server Configuration

These are some notes on the configuration of the Asterisk/FreePBX server.

## Server Software/Hardware
Latest version of RaspPBX distro, RPi Model 3B(+?)

## Additional software installed
- `python3-pip`
- `pip3 install pyst2` (Python AGI scripting interface)
- `apt install default-jdk` (For running Java text games)
- `apt install espeak` (For text-to-speech)
- possibly others, these are the main ones though

## Asterisk dialplan
```
exten => 1000,1,Answer()
exten => 1000,2,AGI(game2asterisk/game2asterisk.py)
```

## Asterisk Server File Layout
- All files in agi-bin/game2asterisk
- file paths adjustable in python scripts
- must create directory nr_game2asterisk in asterisk sounds directory