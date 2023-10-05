'''
    Bundle management module
'''
import numpy as np
import warnings
from enum import Enum, auto
from typing import Optional
from qpsolvers import solve_qp
from algormeter.tools import counter, dbx

warnings.filterwarnings(action='error')
warnings.filterwarnings(action='ignore', category = UserWarning, message='.*Converted.*')
warnings.filterwarnings(action='once', category = UserWarning, message='.*maximum iterations reached.*')
warnings.filterwarnings(action='once', category = UserWarning, message='.*solved inaccurate.*')
warnings.filterwarnings(action='ignore', category = UserWarning,message='.*box cone proj hit maximum.*')
warnings.filterwarnings(action='once', category = UserWarning, message='.*INFEASIBLE_INACCURATE.*')
warnings.filterwarnings(action='once', category = UserWarning, message='.*SOLVED_INACCURATE.*')


class BundleElement :
    def __init__(self,alpha : np.ndarray, beta : float, kind: Enum, lamb: float = 0):
        self.alpha = np.array(alpha,dtype=float)
        self.beta = beta[0].astype(float) if isinstance(beta,np.ndarray) else float(beta)
        self.kind = kind
        self.lamb = lamb

    def __repr__(self):
        return f'alpha:{self.alpha}\n\tbeta:{self.beta} kind:{self.kind} lamb:{self.lamb}\n'

class Bundle :
    def __init__(self, lst = None):
        self.elems = [] if lst is None else lst
        self.qpstat = {} # Quadratic Problem Stat. key = enum G columns, val=# 

    def __repr__(self):
        s = '{\n'
        for i,e in enumerate(self.elems):
            s += f'idx: {i}, {e}'
        return s+'}\n'

    def stat(self):
        if len(self.qpstat) > 0:
            s, m, e = 0, 0, 0
            for k,v in self.qpstat.items():
                s += k*v
                e += v
                if k > m:
                    m = k

            counter.log(str(round(s/e,1)), 'avgRow', cls='qp')
            counter.log(str(m),'maxRow', cls='qp')       

    def append(self,alpha : np.ndarray, beta : float, kind: Enum, lamb: float = 0.):
        self.elems.append(BundleElement(alpha,beta,kind,lamb))

    def appendItem(self, elem : BundleElement):
        self.elems.append(elem)

    def deleteByKind(self,kinds: list[Enum]) -> None: 
        self.elems = [e for e in self.elems if e.kind not in kinds]
    
    def getFirstOfKind(self,kinds: list[Enum]) -> Optional[BundleElement]:
        for e in self.elems:
            if e.kind in kinds:
                return e
        return None

    def deleteByLambdaLessAndNoKinds(self,tol: float, nokinds: list[Enum]) -> None:
        self.elems = [e for e in self.elems if e.lamb > tol and e.kind not in nokinds]

    def reset(self):
        self.elems.clear()

    def scan(self): 
        for e in self.elems:
            yield e

    def solve(self, rho:float, kinds: Optional[list [Enum]] = None, MM: Optional[np.ndarray] = None):

        G0, B0 = zip(*[[el.alpha, el.beta] for el in self.elems if kinds is None or el.kind in kinds])

        match c := len(G0):
            case 0:
                raise ValueError ('Empty bundle')
            case 1: 
                for el in self.elems:
                    if kinds is None or el.kind in kinds:
                        self.elems[0].lamb = 1 # affinchè non venga scartata
                        
                counter.up('1C', cls='qp')
                gg = np.array(G0[0])
                bb = np.array([0])
                return gg, bb
            case 2: 
                counter.up('2C', cls='qp')

        self.qpstat[c] = self.qpstat[c]+1 if c in self.qpstat else 1

        counter.up('solv', cls='qp')
        G=np.array(G0, dtype=float).T
        B=np.array(B0, dtype=float)
        dbx.print('Matrix G:\n',G,'\nB:',B,'rho:',rho) 

        if MM is None:
            P = G.T @ G * rho
        else:
            P = G.T @ MM @ G * rho
            
        _,l = G.shape
        q = B
        A = np.ones(l)
        b = np.array([1.])
        lb = np.zeros(l) 
        ub = np.ones(l)

        #QP Solver
        # https://scaron.info/doc/qpsolvers/
        # https://github.com/stephane-caron/qpsolvers
        # https://osqp.org/docs/index.html
        # https://www.cvxgrp.org/scs/index.html

        # 'ecos', 'osqp', 'proxqp', 'quadprog', 'scs'
        lam = solve_qp(P, q, None, None, A, b ,lb,ub, solver='scs') 
        # lam = solve_qp(P, q, None, None, A, b ,lb,ub, solver='gurobi') 
        if lam is None:
            counter.up('Fail', cls='qp')
            lam = np.ones(c)/c # kick off
        if (lam < 0.).any():
            # lam[lam < 0] = 0
            counter.up('lb<0', cls='qp')
            dbx.print('lam < 0')
        for i, e in enumerate(self.elems) :
            if kinds is None or e.kind in kinds:
                e.lamb  = lam[i]
            else:
                e.lamb  = 0.

        gg = G @ lam
        bb = B @ lam
        dbx.print('lam:',lam, 'gg:',gg, 'bb:',bb)
        return gg,bb

    def sortByLamb(self,reverse: bool = False):
        self.elems.sort(key=lambda x : x.lamb,reverse= reverse)

    def __len__(self):
        return len(self.elems)


if __name__ == "__main__":

    class BEK(Enum): # Bundle Element Kind
        A = auto()
        B = auto()
        C = auto()
        D = auto()
        
    x1 = np.arange(3)
    x2 = np.arange(3)*2
    b=1

    lst = [BundleElement(x1,b,BEK.A, lamb=2),BundleElement(x2,b*2,BEK.B, 4)]
    bundle = Bundle(lst)
    bundle.append(x1,b*4,BEK.B)
    bundle.append(x1,b*4,BEK.C)
    # # bundle.deleteByKind(BEK.C)
    # # print(bundle.G)
    # for e in bundle.scan():
    #     print(e.alpha, e.beta)
    #     e.beta = 7
    #     e.alpha = e.alpha +10
    # for e in bundle.scan():
    #     print(e.alpha, e.beta)
    # # pass

    print(bundle)
    # bundle.sortByLamb(reverse=True)

    # for i, e in enumerate(bundle.elems):
    for e in (bundle.elems):
        if e.kind == BEK.B:
            e.kind = BEK.D

    bundle.elems = [e for e in bundle.elems if e.kind == BEK.D ]

    print(bundle)



    print(len(bundle))
