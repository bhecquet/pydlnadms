
from backend.pydlnadms.fileManagement.FileTree import FileTree
 
treeBuilder = FileTree([], {'test': ['/home/worm/Videos/SauveTest']})
tree = treeBuilder.buildTree()
print(tree)
# FileTree.getInstance('/Videos/Avatar HD.ts')
from backend.pydlnadms.fileManagement.Scanner import Scanner
  
s = Scanner(['/home/worm/Videos/SauveTest'])
s.start()