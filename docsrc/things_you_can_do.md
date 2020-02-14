This document lists a few things you can easily do with stream2py, 
so you get an idea of what stream2py is designed for, 
and get inspiration for other things to do. 


# Get audio segments when ever I chose

In a nutshell:
- I launch the system
- I can grab an segment of the most recent audio by hitting a key

Details and options
- I specify a what audio source I want to use (if there's not an obvious single choice).
- I can specify the sample rate (but there's a default one)
- I get my audio in the form of a numpy array of sample (and could specify what type (int16, int32, float32, float64)
- I can choose a chunk size, or just determine a size in advance so I don't have to specify it every time
- I can have the audio be saved in timestamped files, with a choice of timestamp and audio file formats, specified in advance

## Potential applications

### Record an audio event... after it occured

Say you want to record sneezes as they happen in your open space office. You can record timestamped audio continuously, 
and when you hear a sneeze, quickly jot down the time, and go find and extract that sound later. 
Or... you can be less silly, and instead click a button, and only then will the audio be recorded. 
The problem is, a sneeze's life is short. 
A lot of time passes between the moment the sneeze is born, and ides, 
and moment you notice, and go find that button to click. 
But that's alright, you have a buffer, and can record as much of the "recent past" 
as the buffer allows.

### Triggering audio recording automatically.

A process (buffer reader) takes timestamped chunks off of the buffer automatically and regularly, 
analyzes them, and if certain conditions are met, 
it will grab a bigger recent chunk of data and save it in a file 
(so as to save the event along with a bit more context). 
The condition could be as complex as a event or outlier detection, 
or be a very simple acoustic event such as a burst 
(useful for recording potential breakage, gunshots, sneezes etc.). 




