class Sections():
    
    def __init__(self,Fc,Fy,E_s,A_steel,d_steel,Poly,Ref):
        self.fc = Fc
        self.fy = Fy
        self.Es = E_s
        self.As = A_steel
        self.ds = d_steel
        self.n_s = len(self.As)
        self.poly = Poly
        self.ref = Ref
        self.c = None
        self.Cc = None
        self.d = None
        self.et = None
        self.es = None
        self.fs = None
        self.Fs = None
        self.b1 = None
        self.a = None
        self.dt = None
        self.Pn = None
        self.Mn = None
        self.fi = None
        self.fig1 = None
        self.fig2 = None
    
    def Comp_defo(self,c):
        from Packages.CP import Cent_plas
        from shapely import Polygon, LineString, intersection
        from shapely.ops import split
        import numpy as np

        if(175<=self.fc<=280):
            β1 = 0.85
        elif(280<self.fc<550):
            β1 = 0.85-0.05*(self.fc-280)/70
        elif(self.fc>=550):
            β1 = 0.65

        self.b1 = β1
        a = β1*c
        self.a = a
        #print(a)

        section = Polygon(self.poly)
        x, y = section.exterior.xy
        #plt.figure()
        #plt.plot(x, y, color='blue')  # Plot the exterior of the polygon
        #plt.fill(x, y, color='lightblue', alpha=0.5)

        x_s = []
        for coord in self.poly:
            x_s.append(coord[0])
        x_min = min(x_s)
        x_max = max(x_s)

        line = LineString([(x_min,-a),(x_max,-a)])

        witney_sec = split(section,line).geoms[0]
        x,y = witney_sec.exterior.xy
        #plt.plot(x,y,color='gray')
        #plt.fill(x, y, color='black', alpha=0.5)

        line_c = intersection(section,line)
        x,y = line_c.xy
        #plt.plot(x,y,color='green')

        Ac = section.area
        cen_c = section.centroid.y
        #print(cen_c)

        Aw = witney_sec.area
        self.Aw = Aw
        cen_w = witney_sec.centroid.y

        #Some params

        n_s = len(self.ds)
        dt = self.ds[-1]
        self.dt = dt

        et = abs(0.003*(c-dt)/c)
        ey = self.fy/self.Es
        self.ey = ey

        #Reduction factor
        if(self.ref=="Espirales"):
            a = 0.75
            b = 0.15
        elif(self.ref=="Otro"):
            a = 0.65
            b = 0.25

        if(et<ey):
            fi = a
        elif(ey<et<0.005):
            fi =  a + b*(et-ey)/(0.005-ey)
        elif(et>=0.005):
            fi = 0.9
        self.fi = fi
        
        #Calcs

        Cc = 0.85*self.fc*Aw/1000
        self.Cc = Cc

        CP = round(Cent_plas(self.fc,self.fy,Ac,cen_c,n_s,self.As,self.ds),1)

        Pn = Cc
        Mn = Cc*(CP-cen_w)

        es_l = []
        fs_l = []
        Fs_l = []
        for i in range(n_s):
            es = round(0.003*(c-self.ds[i])/c,4)
            es_l.append(es)
            #print(f"es{str(i+1)}=0.003({str(c)}-{str(self.ds[i])})/{str(c)}={str(es)}")
            if(abs(es)<ey):
                fs = self.Es*es
                #print(f"{str(es)}<{str(ey)}")
            elif(abs(es)>=ey):
                fs = np.sign(es)*self.fy
                #print(f"{str(es)}>={str(ey)}")
            #print(f"fs{str(i+1)}={str(round(fs,2))}")
            fs_l.append(fs)
            Fs = fs*self.As[i]/1000
            Fs_l.append(Fs)
            #print(f"Fs{str(i+1)}={str(Fs)}")

            Pn = Pn + Fs
            Mn = Mn + Fs*(CP-self.ds[i])

        #print(Pn)
        #print(Mn)
        self.es = es_l
        self.fs = fs_l
        self.Fs = Fs_l
        self.c = c
        self.et = -et
        self.Pn = Pn
        self.Mn = Mn/100
        return 0
    
    def d_dis(self,c):
        d = 0
        at = 0
        for i in range(self.n_s):
            if(self.ds[i]>c):
                d = d + self.ds[i]*self.As[i]
                at = at + self.As[i]
        d = d/at
        self.d = d
        return 0
    
    def Plot_comp_defo(self):
        import matplotlib.pyplot as plt
        from shapely import Polygon, LineString, intersection
        from shapely.ops import split
        import numpy as np

        section = Polygon(self.poly)
        x, y = section.exterior.xy
        fig1,ax1 = plt.subplots()
        ax1.plot(x, y, color='blue')  # Plot the exterior of the polygon
        ax1.fill(x, y, color='lightblue', alpha=0.5)

        x_s = []
        for coord in self.poly:
            x_s.append(coord[0])
        x_min = min(x_s)
        x_max = max(x_s)

        line = LineString([(x_min,-self.a),(x_max,-self.a)])

        witney_sec = split(section,line).geoms[0]
        x,y = witney_sec.exterior.xy
        ax1.plot(x,y,color='red')
        ax1.fill(x, y, color='red', alpha=0.5)

        line_c = intersection(section,line)
        x,y = line_c.xy
        ax1.plot(x,y,color='red')

        zeros = [0]*self.n_s
        ds_array = -1*np.array(self.ds)
        ax1.scatter(zeros,ds_array)

        for i,a_s in enumerate(self.As):
            ax1.annotate(f"{str(round(a_s,2))}cm2", (zeros[i],ds_array[i]))

        plt.axis('off')

        fig2,ax2 = plt.subplots()

        #y_s = []
        #for coord in self.poly:
        #    y_s.append(coord[1])
        #y_min = min(y_s)
        #y_max = max(y_s)
        #depth = y_max-y_min

        depth = abs(self.ds[-1])

        ax2.plot((0,0,0.003,self.et,0),(0,depth,depth,0,0))
        ax2.annotate("ec=0.003",(0.0008,1*depth))
        for i in range(self.n_s):
            ax2.plot((0,self.es[i]),(depth-self.ds[i],depth-self.ds[i]))
            ax2.annotate(f"{str(self.es[i])}",(self.es[i]*0.75,(depth-self.ds[i])))

        plt.axis('off')

        self.fig1 = fig1
        self.fig2 = fig2

    def Save_comp_defo(self,path):
        import matplotlib.pyplot as plt
        try:
            self.fig1.savefig(f"{path}/Beam sect")
            self.fig2.savefig(f"{path}/Beam deformation compatibility")
        except:
            print("No figure specified")
