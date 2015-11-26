from copy import deepcopy

'''
    Global Optimisation
        of a combinatory problem
        using custom Genetic Algorithm
    
    Usage:
        optimiser = Optimiser()
        # vi is a candidate solution e.g. [1,2,3]
        optimiser.reset(costfn=, printfn=, seed=[v1,v2,...])
        optimiser.start()
        vs = optimiser.getSolution()
        
    Tips:
        try different settings
        seed with good candidate
        you may want to try unseeded (or with random seed)
            to avoid bias and falling into the same regions
            then seed with the best candidates
'''
from random import shuffle, randint, random
class Optimiser:
    
    def __init__(self):
        pass
    
    def reset(self, costfn, printfn, seed, popSize=None, ln=None, maxGen=10000):
        self.costfn = costfn
        self.printfn = printfn
        self.seed = deepcopy(seed) if seed else []
        self.ln = ln or len(self.seed[0])

        if popSize is None:
            popSize = self.ln * 3
        self.popSize = popSize
        
        self.maxGen = maxGen
        self.maxGen = 5000
        self.improvementGap = 1000
        
        self.crossOverRate = 0.7
        self.mutationRate = 0.1
        
        self.stopReason = ''
        
    def start(self):
        print '-' * 20
        print 'START'
        self.prepare()
        
        self.gen = 0
        while True:
            self.computeFitness()
            self.gen += 1
            
            if self.gen % 100 == 0:
                print 'Gen %s. Cost %s. Best: %s. Pop: %s' % (self.gen, self.getPopCost(), self.getBestCost(), len(self.vs))

            if self.canStop():
                break
            
            vs = [self.bestV]
            while len(vs) < self.popSize:
                v1, v2 = self.select()
                v3, v4 = self.crossOver(v1, v2)
                #v3 = self.mutate(v3)
                vs.append(self.mutate(v3))
                vs.append(self.mutate(v4))
            vs = vs[0:self.popSize]
            self.vs = vs
            
        self.printGenSummary()

    def computeFitness(self):
        showSum = 0
        for i in range(0, len(self.vs)):
            self.popCosts[i] = self.costfn(self.vs[i])
            if self.bestCost is None or self.popCosts[i] < self.bestCost:
                self.bestCost = self.popCosts[i]
                self.bestV = self.vs[i]
                self.bestGen = self.gen
                showSum = 1
        
        self.fitnesses = [[self.vs[i], 1.0/(self.popCosts[i] or 0.1)] for i in range(0, len(self.vs))]
        sumFit = sum([f[1] for f in self.fitnesses])
        self.fitnesses = [[f[0], f[1]/sumFit] for f in self.fitnesses]

        if showSum:
            self.printGenSummary()

    def printGenSummary(self):
        print 'Gen %s. Cost %s. Best: %s. Pop: %s' % (self.gen, self.getPopCost(), self.getBestCost(), len(self.vs))
        
    def selectOne(self):
        # roulette wheel selection
        ret = self.vs[0]
        r = random()
        for f in self.fitnesses:
            r = r - f[1]
            if r < 0:
                ret = f[0]
                break
        return ret

    def select(self):
        return self.selectOne(), self.selectOne()

    def crossOver(self, v1, v2):
        if random() < self.crossOverRate:
            point = randint(1, len(v1)-2)
            v3 = v1[0:point]
            v3 += [s for s in v2 if s not in v3]
            v4 = v2[0:point]
            v4 += [s for s in v1 if s not in v4]
        else:
            #ret = v1[:]
            v3 = v1[:]
            v4 = v2[:]
            
        return v3, v4
        
    def mutate(self, v):
        ret = v
        for i in range(0, self.ln):
            if random() < self.mutationRate:
                #ri = randint(0, self.ln - 1)
                #ret[i], ret[ri] = ret[ri], ret[i]
                ri = i + 1
                if random() > 0.8: ri = randint(0, self.ln - 1)
                if ri >= self.ln: ri = 0
                ret[i], ret[ri] = ret[ri], ret[i]
            
        return ret

    def getPopCost(self):
        return min(self.popCosts)
        
    def getBestCost(self):
        return self.bestCost

    def canStop(self):
        ret = False
        
        if (self.gen >= self.maxGen) and ((self.gen - self.bestGen) > self.improvementGap):
            ret = True
            self.stopReason = 'max iteration'
        
        return ret
    
    def prepare(self):
        self.stopReason = ''
        self.bestV = None
        self.bestCost = None
        self.bestGen = 0
        
        # create population
        self.vs = deepcopy(self.seed)
        
        # make up vectors to meet pop size
        while len(self.vs) < self.popSize:
            self.vs.append(self.getRandomVector())
            
        # truncate to match pop size
        self.vs = self.vs[0:self.popSize]
    
        self.popCosts = [0] * len(self.vs)
    
    def getRandomVector(self):
        ret = range(0, self.ln)
        shuffle(ret)
        return ret
    
    def getSolution(self):
        return self.bestV

