# README.md

### Branch `feature/tagging` 
`feature/tagging` implements a generic style tagging of Kraken's messages by mapping the channelID to the stream to which it is referencing. 

`feature/routing` using the channel map, dispatch messages to their respective parse functions based on their tagged stream type. 

`feature/store` condense parse stubs into a stream_validator to verify the streams before porting onto the PI.

### `examples/`
Includes sample data outputs from websocket for data progression tracking with version control.

# Status
as it stands, parsing has been dropped from the work flow. **no need to parse to add time stamps.** 
routing logic ported into the stream_validator function to ensure messages are receiving proper.

current task: create a wrapper for each message to be stored on disk with proper metadata
metadata: recv_time, channel_id, stream_type, pair, interval, message.

the next step is to run the final storage after writing the wrapper code. 