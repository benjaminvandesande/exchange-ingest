# README.md

### Branch `feature/tagging` 
`feature/tagging` implements a generic style tagging of Kraken's messages by mapping the channelID to the stream to which it is referencing. 

`feature/routing` using the channel map, dispatch messages to their respective parse functions based on their tagged stream type. 


### `examples/`
Includes sample data outputs from websocket for data progression tracking with version control.