#!/usr/bin/env python3
"""Build the Chinese translation .mod from the original Workshop .mod.

Usage:
  python build_translation.py "Informative WANTED Posters.mod" "Informative WANTED Posters CN.mod"
"""
from pathlib import Path
import json, struct, sys

def read_str(b,o):
    n=struct.unpack_from("<I",b,o)[0]; o+=4
    raw=b[o:o+n]; o+=n
    return raw.decode("utf-8"),o

def pack_str(s):
    raw=s.encode("utf-8")
    return struct.pack("<I",len(raw))+raw

def parse_record(b,o):
    unknown,typ,id_=struct.unpack_from("<3i",b,o);o+=12
    name,o=read_str(b,o); sid,o=read_str(b,o); change=struct.unpack_from("<i",b,o)[0];o+=4
    fields={}
    for kind,fmt,size in [("bool","<?",1),("float","<f",4),("long","<i",4)]:
        c=struct.unpack_from("<i",b,o)[0];o+=4;arr=[]
        for _ in range(c):
            k,o=read_str(b,o);v=struct.unpack_from(fmt,b,o)[0];o+=size;arr.append((k,v))
        fields[kind]=arr
    for kind,n in [("vec3",3),("vec4",4)]:
        c=struct.unpack_from("<i",b,o)[0];o+=4;arr=[]
        for _ in range(c):
            k,o=read_str(b,o);v=struct.unpack_from("<"+"f"*n,b,o);o+=4*n;arr.append((k,v))
        fields[kind]=arr
    for kind in ["string","filename"]:
        c=struct.unpack_from("<i",b,o)[0];o+=4;arr=[]
        for _ in range(c):
            k,o=read_str(b,o);v,o=read_str(b,o);arr.append((k,v))
        fields[kind]=arr
    c=struct.unpack_from("<i",b,o)[0];o+=4
    for _ in range(c):
        _,o=read_str(b,o);ic=struct.unpack_from("<i",b,o)[0];o+=4
        for _ in range(ic):
            _,o=read_str(b,o);o+=12
    c=struct.unpack_from("<i",b,o)[0];o+=4
    for _ in range(c):
        _,o=read_str(b,o);_,o=read_str(b,o);o+=28
        sc=struct.unpack_from("<i",b,o)[0];o+=4
        for _ in range(sc): _,o=read_str(b,o)
    return (unknown,typ,id_,name,sid,change,fields)

def pack_record(r,name,description):
    _,typ,_,old_name,sid,_,_=r
    out=bytearray(struct.pack("<3i",0,typ,0))
    out += pack_str(name)+pack_str(sid)
    out += struct.pack("<i",-2147483645 if name != old_name else -2147483647)
    out += struct.pack("<5i",0,0,0,0,0)
    if description is None:
        out += struct.pack("<i",0)
    else:
        out += struct.pack("<i",1)+pack_str("description")+pack_str(description)
    out += struct.pack("<3i",0,0,0)
    return bytes(out)

def main(src,dst):
    root=Path(__file__).resolve().parents[1]
    tr=json.loads((root/"translation.json").read_text(encoding="utf-8"))
    b=Path(src).read_bytes()
    if struct.unpack_from("<i",b,0)[0] != 16:
        raise ValueError("Only Kenshi .mod file type 16 is supported.")
    o=4
    version=struct.unpack_from("<i",b,o)[0];o+=4
    for _ in range(4): _,o=read_str(b,o)
    o+=4
    rc=struct.unpack_from("<i",b,o)[0];o+=4
    records=[]
    for _ in range(rc):
        st=o; r=parse_record(b,o); records.append(r)
        # Re-run the parser from the known start to get its end position.
        # This avoids depending on private parser state.
        o=st
        _,typ,id_=struct.unpack_from("<3i",b,o);o+=12
        _,o=read_str(b,o);_,o=read_str(b,o);o+=4
        for fmt,size in [("<?",1),("<f",4),("<i",4)]:
            c=struct.unpack_from("<i",b,o)[0];o+=4
            for _ in range(c): _,o=read_str(b,o);o+=size
        for n in (3,4):
            c=struct.unpack_from("<i",b,o)[0];o+=4
            for _ in range(c): _,o=read_str(b,o);o+=4*n
        for _ in range(2):
            c=struct.unpack_from("<i",b,o)[0];o+=4
            for _ in range(c): _,o=read_str(b,o);_,o=read_str(b,o)
        c=struct.unpack_from("<i",b,o)[0];o+=4
        for _ in range(c):
            _,o=read_str(b,o);ic=struct.unpack_from("<i",b,o)[0];o+=4
            for _ in range(ic): _,o=read_str(b,o);o+=12
        c=struct.unpack_from("<i",b,o)[0];o+=4
        for _ in range(c):
            _,o=read_str(b,o);_,o=read_str(b,o);o+=28
            sc=struct.unpack_from("<i",b,o)[0];o+=4
            for _ in range(sc): _,o=read_str(b,o)
    out=bytearray(struct.pack("<2i",16,3))
    for s in ["SonicMiso",tr["header_description"],
              "Informative WANTED Posters.mod,Dialogue.mod,rebirth.mod","gamedata.base"]:
        out += pack_str(s)
    out += struct.pack("<2i",5007306,len(records))
    for i,r in enumerate(records):
        out += pack_record(r,tr["names"].get(r[3],r[3]),tr["descriptions"].get(str(i)))
    Path(dst).write_bytes(out)

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("Usage: python build_translation.py <original.mod> <translated.mod>")
    main(sys.argv[1],sys.argv[2])
