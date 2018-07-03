import subprocess
import re
import os
import threading

class MountUtility(object):
    
    mountedPaths = None
    devicesToMount = None
    tmpMountedDevices = None
    mountLock = threading.Lock()

    @staticmethod
    def __getMountedDevices():
        regMount = re.compile(".* on (.*) type .*")
        out = subprocess.check_output(['mount'])
        return (regMount.findall(bytes.decode(out)))
        
    @staticmethod
    def __getDevicesToMount():
        regFstab = re.compile("^.*? (.*?) \w+.*")
        devicesToMount = []
        
        with open('/etc/fstab', 'r') as fstab:
            for line in fstab:
                if line.startswith('#'):
                    continue
            
                if regFstab.search(line) is not None:
                    devicesToMount.append(regFstab.search(line).groups()[0])
        
        return devicesToMount
        
    @classmethod
    def _mount(cls, path):
        if not path.endswith('/'):
            path += '/'
        with cls.mountLock:
            subprocess.check_call(["sudo", "mount", path])
        
    @classmethod
    def _umount(cls, path):
        if not path.endswith('/'):
            path += '/'
        with cls.mountLock:
            subprocess.check_call(["sudo", "umount", path])
    
    @classmethod
    def checkMount(cls, path):
        """
        check if a folder is already mounted, and if not, mount it
        It mounts the root folder referenced in fstab
        """
        
        # in case of symlink, get the real path to mount it
        if os.path.islink(path):
            path = os.path.realpath(path) 
        
        if cls.mountedPaths is None:
            cls.mountedPaths = cls.__getMountedDevices()
            cls.devicesToMount = cls.__getDevicesToMount()
           
        for tmPath in cls.devicesToMount:
            if tmPath in cls.mountedPaths:
                continue
          
            if path.startswith(tmPath):
                try:
                    cls._mount(tmPath)
                except Exception as err:
                    print(err)
                else:
                    cls.mountedPaths = cls.__getMountedDevices()    
                break
            
    @classmethod
    def mountRootFolders(cls, rootFolder):
        """
        mounts all folders under root directory of the server
        """
        if cls.mountedPaths is None:
            cls.mountedPaths = cls.__getMountedDevices()
            cls.devicesToMount = cls.__getDevicesToMount()
            
        for tmPath in cls.devicesToMount:
            if tmPath in cls.mountedPaths:
                continue
          
            if tmPath.startswith(rootFolder) or rootFolder.startswith(tmPath):
                try:
                    cls._mount(tmPath)
                except Exception as err:
                    print(err)
        
        cls.mountedPaths = cls.__getMountedDevices()
        
    @classmethod
    def umountRootFolders(cls, rootFolder):
        """
        umounts all folders under root directory of the server
        """
        if cls.tmpMountedDevices is None:
            return
            
        for tmPath in cls.tmpMountedDevices:
            try:
                cls._umount(tmPath)
            except Exception as err:
                print(err)
        cls.tmpMountedDevices = None
        
        cls.mountedPaths = cls.__getMountedDevices()
         

    

 
