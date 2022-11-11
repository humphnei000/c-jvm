import pathlib
from graphlib import TopologicalSorter
from abc import ABC, abstractmethod
import os

class Target(ABC):
    pass
class Action(ABC):
    @abstractmethod
    def run(self):
        pass

class PathTarget(Target):
    def __init__(self, path):
        self._path = pathlib.Path(path);
    def __eq__(self, other):
        return isinstance(other, PathTarget) and self._path == other._path
    def __hash__(self):
        return hash(self._path)
    def getPath(self):
        return self._path
    def __repr__(self):
        return f"PathTarget(path={self._path})"
class NameTarget(Target):
    def __init__(self, name):
        self._name = name;
    def __eq__(self, other):
        return isinstance(other, NameTarget) and self._name == other._name
    def __hash__(self):
        return hash(self._name)
    def __repr__(self):
        return f"NameTarget(name={repr(self._name)})"
class CommandListAction(Action):
    def __init__(self, commands):
        self._commands = commands
    def run(self):
        for command in self._commands:
            os.system(command)
    def __repr__(self):
        return f"CommandListAction(commands={self._commands})"
class Recipe(ABC):
    @abstractmethod
    def hasOutput(self, target): #returns bool
        pass

    @abstractmethod
    def getDependencies(self, target): #returns set
        pass

    @abstractmethod
    def getAction(self, target):
        pass
class BuildStep:
    def __init__(self, target, action, deps):
        assert not isinstance(action, Recipe)
        
        self.target = target,
        self.action = action
        self.deps = deps
    def __repr__(self):
        return (
            "BuildStep("
            f"target={self.target}, "
            f"action={self.action}, "
            f"deps={self.deps}"
            ")"
        )

class RecipeList:
    def __init__(self, recipes):
        self.recipes = list(recipes)
    def getRecipeByTarget(self, target):
        for recipe in self.recipes:
            if recipe.hasOutput(target):
                return recipe
        return None
    def hasRecipeForTarget(self, target):
        return self.getRecipeByTarget(target) != None
    def getDependenciesOfTarget(self, target):
        recipe = self.getRecipeByTarget(target)

        if recipe != None:
            return recipe.getDependencies(target)
        return set()
class DependencySolver:
    def __init__(self, recipeList):
        self.recipeList = recipeList
        self.depGraph = {}
        self.unprocessedDependencies = set()
    def addDependency(self, target):
        if target not in self.depGraph:
            self.unprocessedDependencies.add(target)
    def popUnprocessedDependency(self):
        target = None
        for t in self.unprocessedDependencies:
            target = t
        self.unprocessedDependencies.remove(target)
        return target
    def hasUnprocessedDependencies(self):
        return len(self.unprocessedDependencies) != 0
    def makeGraph(self, mainTarget):
        self.addDependency(mainTarget)

        while self.hasUnprocessedDependencies():
            target = self.popUnprocessedDependency()
            deps = self.recipeList.getDependenciesOfTarget(target)
            
            self.depGraph[target] = deps
            for dep in deps:
                self.addDependency(dep)
    def makeSteps(self):
        steps = []
        for target in TopologicalSorter(self.depGraph).static_order():
            recipe = self.recipeList.getRecipeByTarget(target)
            if recipe != None:
                steps.append(BuildStep(
                        target,
                        recipe.getAction(target),
                        self.depGraph[target]
                ))
        return steps
    def solve(self, mainTarget):
        self.makeGraph(mainTarget)
        return self.makeSteps()
def makeBuildSteps(mainTarget, recipeList):
    return DependencySolver(recipeList).solve(mainTarget)

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
        
        return CommandListAction([
            f"{CC} {CFLAGS} {LDFLAGS} {ofilelist} -o {progfile}"
        ])

CC = "gcc"
CFLAGS="-g -O2 -Werror" #-std=c99
LDFLAGS="-lm"
SRCPATH = pathlib.Path("./src")
BUILDPATH = pathlib.Path("./build")

RECIPES = RecipeList([
    ProgramRecipe("jvm")
])

MAINTARGET = PathTarget("./build/jvm")

for step in makeBuildSteps(MAINTARGET, RECIPES):
    print(step)