import pathlib
from graphlib import TopologicalSorter
from abc import ABC, abstractmethod
import os

class BaseBuildDebugger(ABC):
    @abstractmethod
    def useDepGraph(self, graph):
        pass
    @abstractmethod
    def useCommand(self, command):
        pass
class BuildDebugger(BaseBuildDebugger):
    def useDepGraph(self, graph):
        print("-------- DEPENDENCY GRAPH --------")
        acc = ""
        for target in graph:
            acc += f"{target}:\n"
            for dep in graph[target]:
                acc += f"    {dep}\n"
        print(acc.strip())
    def useCommand(self, command):
        print("running "+repr(command))
class NullBuildDebugger(BaseBuildDebugger):
    def useDepGraph(self, graph):
        pass
    def useCommand(self, command):
        pass
    
DBG = BuildDebugger()

#core

class Target(ABC):
    @abstractmethod
    def checkExists(self):
        pass
class Action(ABC):
    @abstractmethod
    def run(self):
        pass
class BuildStep:
    def __init__(self, target, action, deps):
        assert not isinstance(action, Recipe)
        
        self.target = target
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
        DBG.useDepGraph(self.depGraph)
        return self.makeSteps()
def makeBuildSteps(mainTarget, recipeList):
    return DependencySolver(recipeList).solve(mainTarget)

#not core

#targets
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
    def checkExists(self):
        return self._path.exists()
class NameTarget(Target):
    def __init__(self, name):
        self._name = name;
    def __eq__(self, other):
        return isinstance(other, NameTarget) and self._name == other._name
    def __hash__(self):
        return hash(self._name)
    def __repr__(self):
        return f"NameTarget(name={repr(self._name)})"
    def checkExists(self):
        return True #as long as the order of build steps are followed, this dependency always exists

#actions
class CommandAction(Action):
    def __init__(self, command):
        self._command = command
    def run(self):
        DBG.useCommand(self._command)
        os.system(self._command)
    def __repr__(self):
        return f"CommandListAction(command={repr(self._command)})"
class EnsurePathAction(Action):
    def __init__(self, path):
        self._path = path
    def run(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
    def __repr__(self):
        return f"EnsurePathAction(path={self._path})"
class ActionList(Action):
    def __init__(self, actionList):
        self._actions = actionList
    def run(self):
        for action in self._actions:
            action.run()
    def __repr__(self):
        return f"ActionList(actions={self._actions})"