import zlib
import pickle

class Zlib:
    
    @staticmethod 
    def compressObject(Obj) -> bytes:
        """Compresses an object using zlib and returns the compressed bytes.
        """
        data = pickle.dumps(Obj)
        compressed_data = zlib.compress(data, 9)
        return compressed_data
    
    @staticmethod
    def uncompressObject(compressed_data: bytes):
        """Uncompresses the given compressed bytes and returns the original object.
        """
        data = zlib.decompress(compressed_data)
        Obj = pickle.loads(data)
        return Obj