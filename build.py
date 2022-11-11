from buildlib import *
from pathlib import Path
import os

class ProgramRecipe(Recipe):
    def __init__(self, progName):
        self._progPath = BUILDPATH / progName
        self._ofiles = None
    def _getOFiles(self):
        if self._ofiles == None:
            self._ofiles = set()
            for path in SRCPATH.glob("**/*.c"):
                self._ofiles.add(PathTarget(
                    BUILDPATH.joinpath(path.relative_to(SRCPATH)).with_suffix('.o')
                ))
        return self._ofiles
    def hasOutput(self, target):
        return target == PathTarget(self._progPath)
    def getDependencies(self, target):
        assert self.hasOutput(target)
        return self._getOFiles()
    def getAction(self, target):
        ofilelist = [str(path.getPath().resolve()) for path in self._getOFiles()]
        ofilelist = ' '.join(ofilelist)
        progfile = str(self._progPath.resolve())
        
        return CommandAction(
            f"{CC} {CFLAGS} {LDFLAGS} {ofilelist} -o {progfile}"
        )
class OFileRecipe:
    def __init__(self):
        pass
    def _makeDepPath(self, targPath):
        return (SRCPATH / targPath.relative_to(BUILDPATH)).with_suffix('.c')
    def hasOutput(self,target):
        return isinstance(target, PathTarget) and target.getPath().suffix == ".o"
    def getDependencies(self, target):
        assert self.hasOutput(target)
        
        return set([PathTarget(
            self._makeDepPath(target.getPath())
        )])
    def getAction(self, target):
        assert self.hasOutput(target)
        ofile = str(target.getPath().resolve())
        cfile = str(self._makeDepPath(target.getPath()).resolve())
        
        return CommandAction(
            f"{CC} {CFLAGS} -c {cfile} -o {ofile}"
        )

CC = "gcc"
CFLAGS="-g -O2 -Werror" #-std=c99
LDFLAGS="-lm"
SRCPATH = pathlib.Path("./src")
BUILDPATH = pathlib.Path("./build")

RECIPES = RecipeList([
    ProgramRecipe("out"),
    OFileRecipe()
])

MAINTARGET = PathTarget("./build/out")

#actual building

def ensurePath(path):
    path.parent.mkdir(parents=True, exist_ok=True)
def runStep(step):
    #if isinstance(step.target, PathTarget):
        #ensurePath(step.target.getPath())
    step.action.run()

steps = makeBuildSteps(MAINTARGET, RECIPES)
print("-------- COMMANDS --------")
for step in steps:
    runStep(step)