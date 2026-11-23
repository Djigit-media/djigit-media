import sys, torch, numpy as np, subprocess, json
from transformers import Wav2Vec2ForCTC, AutoProcessor
M='facebook/wav2vec2-xlsr-53-espeak-cv-ft'
proc=AutoProcessor.from_pretrained(M); model=Wav2Vec2ForCTC.from_pretrained(M).eval()
def load(p, ss=None, to=None):
    cmd=['ffmpeg','-v','error']+(['-ss',str(ss)] if ss is not None else [])+(['-to',str(to)] if to is not None else [])+['-i',p,'-ac','1','-ar','16000','-f','f32le','-']
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.float32)
def phon(x):
    iv=proc(x,sampling_rate=16000,return_tensors='pt').input_values
    with torch.no_grad(): lg=model(iv).logits
    return proc.batch_decode(lg.argmax(-1))[0]
if __name__=='__main__':
    for p in sys.argv[1:]: print(p, '|', phon(load(p)))
