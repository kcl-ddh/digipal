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

    def reset(self, costfn, printfn, seed, popSize=None, ln=None, maxGen=5000, lowcost=0.0, improvementGap=1000, replaceSeed=False):
        self.costfn = costfn
        self.printfn = printfn
        self.seed = deepcopy(seed) if seed else []
        self.ln = ln or len(self.seed[0])
        self.replaceSeed = replaceSeed

        if popSize is None:
            popSize = self.ln * 3
        self.popSize = popSize

        self.maxGen = maxGen
        self.improvementGap = improvementGap or 1000
        self.lowcost = lowcost or 0.0

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
                self.printGenSummary()

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
        print self.stopReason

    def computeFitness(self):
        showSum = 0
        for i in range(0, len(self.vs)):
            self.popCosts[i] = self.costfn(self.vs[i])
            if self.bestCost is None or self.popCosts[i] < self.bestCost:
                if self.bestCost is None or (self.bestCost - self.popCosts[i]) > 0.001:
                    self.bestGen = self.gen

                self.bestCost = self.popCosts[i]
                self.bestV = self.vs[i]
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

    def crossOver(self, v1, v2, rate=None):
        if rate is None:
            rate = self.crossOverRate
        if random() < rate:
            return self.crossOverOnePoint(v1, v2)
        else:
            return v1[:], v2[:]

    def crossOverUniform(self, *vo):
        vs = deepcopy(vo)

        for i in range(0, len(vo[0])):
            if random() < 0.2:
                vs[0][i] = None
            else:
                vs[1][i] = None

        #print vo
        #print vs

        vs2 = deepcopy(vs)
        for j in range(0, 2):
            vr = [h for h in vs2[1-j] if h not in vs2[j]]
            vr += [h for h in vo[j] if (h not in vr and h not in vs2[j])]
            for i in range(0, len(vo[0])):
                if vs[j][i] is None: vs[j][i] = vr.pop(0)

        #print vs

        #exit()

        return vs[0], vs[1]

    def crossOverOnePoint(self, v1, v2):
        point = randint(1, len(v1)-2)
        v3 = v1[0:point]
        v3 += [s for s in v2 if s not in v3]
        v4 = v2[0:point]
        v4 += [s for s in v1 if s not in v4]

        return v3, v4

    def mutate(self, v, mutationRate=None):
        ret = v
        if mutationRate is None:
            mutationRate = self.mutationRate
        for i in range(0, self.ln):
            if random() < mutationRate:
                #ri = randint(0, self.ln - 1)
                #ret[i], ret[ri] = ret[ri], ret[i]
                ri = i + 1
                if random() > 0.5: ri = randint(0, self.ln - 1)
                #ri = randint(0, self.ln - 1)
                if ri >= self.ln: ri = 0
                ret[i], ret[ri] = ret[ri], ret[i]

        return ret

    def getPopCost(self):
        return min(self.popCosts)

    def getBestCost(self):
        return self.bestCost

    def canStop(self):
        self.stopReason = ''

        if self.getBestCost() <= self.lowcost:
            self.stopReason = 'low cost'
        #print (self.gen - self.bestGen), self.improvementGap
        if (self.gen >= self.maxGen):
            self.stopReason= 'max iteration'
        if ((self.gen - self.bestGen) > self.improvementGap):
            self.stopReason= 'stagnate'

        return bool(self.stopReason)

    def prepare(self):
        self.stopReason = ''
        self.bestV = None
        self.bestCost = None
        self.bestGen = 0

        # create population
        toRemove = 0
        if self.replaceSeed:
            toRemove = len(self.seed)
        self.vs = deepcopy(self.seed)

        # make up vectors to meet pop size
        while len(self.vs) < self.popSize:
            self.vs.append(self.getRandomVector())
            # TODO: improve this dirty implementation of seed repalcement
            if toRemove:
                self.vs = self.vs[1:]
                toRemove -= 1

        # truncate to match pop size
        self.vs = self.vs[0:self.popSize]

        self.popCosts = [0] * len(self.vs)

    def getRandomVector(self, random=False):
        if random or not self.seed:
            ret = range(0, self.ln)
            shuffle(ret)
        else:
            v1 = self.seed[-1]
            v2 = self.mutate(v1, 0.9)
            v23 = self.crossOver(v1, v2, 1)
            ret = v23[0]
        return ret

    def getSolution(self):
        return self.bestV

