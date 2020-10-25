#game2asterisk

A bridge between text-based games (that use standard in and standard out) and the Asterisk IP PBX. Enables some text-based games to be played over a standard phone call without modification of the game itself. 

## Principle of operation

Most text-based games have common elements, such as entering a number, answering a y/n prompt, or typing a predefined command to change the game state. `game2asterisk` will, when supplied with a file indicating how the text-based interface should be adapted to the phone environment, enable the user to play the game over the phone. To enable a game to work with `game2asterisk`, the user must write a JSON file describing the different prompts the game uses to ask for output and telling `game2asterisk` what kind of input to read from the user. Additionally, this JSON file can specify various transformations that should occur on the game's output before it is read out to the user and/or on the user's input before it is fed to the game.

The sequence can be visualized as a pipeline of operations that is executed on each line:
get line from game -> match reader on line -> apply output transformations -> read transformed output to user -> perform action -> apply input transformation on action -> feed transformed input line to game

## JSON File Example

Here is an example of a basic JSON file that tells `game2asterisk` how to adapt a simple random-number guessing game (see py/rng_game.py) to be played over the phone.

```
{
  "readers": [
    {
      "regex": "Pick a number .*? 9",
      "toRead": "num"
    },
    {
    	"regex": "Pick a number .*? 20",
    	"toRead": "multinum",
    	"inputHint": "Enter a number, followed by the pound key"
    }
  ],
  "target": ["python3", "rng_game.py"]
}
````

## JSON File Details

The JSON file is organized as a list of "readers", which describe the outputs of the game, in most cases the prompts for user input. Additionally, there is a "target" that describes how to run the game. `game2asterisk` works with any text-based game that uses standard input and output, so it can work with games written in Python, Java, C, etc.

### Readers
Readers have the following properties:
- `comment` (optional) - ignored by `game2asterisk`, used to help the user understand what this reader matches.
- `regex` (mandatory) - a regular expression describing (and possibly capturing parts of) one output prompt or other output of the game.
- `action` (mandatory) - the type of action to perform. See actions section.
- `inputHint` (optional) - A hint to read out to the user after the prompt is read. The input hint can be used to help the user understand how to enter their input.
- `outputTransformers` (optional) - Descriptions of transformations to apply on the output from the game, before it is read out loud to the user. Output transformers are used to make the game outputs work better with the text-to-speech. See output transformers section.
- `inputTransformers` (optional) - Descriptions of transformations to apply on the input received from the user (usually numbers dialed on the phone keypad), before it is fed back to the game. Input transformers are used to adapt user input to a different format, for example mapping digits to strings. See input transformers section.


Readers are evaluated one at a time, in the order they are written in the JSON file, to see if their regex matches the current line of game output (readers are evaluated on every line of game output). Once a match is found, no further readers are evaluated. If no match is found, the game output is simply read out loud to the user.

#### Capture Strings
Strings used for the `inputHint` property, for replacement values in output transformers, and for the `processedLiteralReturn` action type can be processed to replace parts of them with the value of given capture groups in the regex that matched on the output from the game. This can be used for more dynamic output. The syntax for capture strings is `${x}`, where `x` is the capture group in the regex from the `regex` property of the reader that matched. For example, if the `regex` property was `player ([0-9]+)`, matching on an output line containing a player number, the capture string `"Hello, player ${1}"` would evaluate to `Hello, player 22` if the game output was `"player 22`.

#### Actions
The possible actions are:
- `num` - read a single digit from the user
- `multinum` - read a multiple-digit number from the user
- `noop` - do nothing
- `processedLiteralReturn` - process the `literal` string for any capture strings and return it without asking the user for any input.


#### Output Transformers
The possible transformers are:
- `replace` - replace the specified capture group (`captureGroup`) in the regex that matched on the game output with the given replacement value (`replacementValue`). `replacementValue` is processed to evaluate any capture string syntax. 
- `replaceEntireString` - replace the entire game output string with the given replacement value (`replacementValue`). `replacementValue` is processed to evaluate any capture string syntax. 


#### Input Transformers
The possible transformers are:
- `digitStrMapping` - map a pressed digit string from the user to a character string. 