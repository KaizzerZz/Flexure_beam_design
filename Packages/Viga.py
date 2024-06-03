from Packages.Sections import Sections
import numpy as np
import copy

As_steels = {"0":0,"3/8":0.71, "1/2":1.29, "5/8":2, "3/4":2.84, "7/8": 3.87, "1":5.1, "1 1/8":6.45}
diam_steels = {"0":0,"3/8":0.9525, "1/2":1.27, "5/8":1.5875, "3/4":1.905, "7/8": 2.2225, "1":2.54, "1 1/8":2.8575}

class Viga():
    def __init__(self,L,fc,fy,Es):
        self.L = L
        self.fc = fc
        self.fy = fy
        self.Es = Es
        self.h = None
        self.bw = None
        self.tw = None
        self.tf = None
        self.poly = None
        self.name = None

    def Rec_section(self,b,h):
        poly = [(b/2,0),(b/2,-h),(-b/2,-h),(-b/2,0)]
        self.h = h
        self.bw = b
        self.poly = poly
        self.name = "Viga Rectangular"
        pass

    def T_section(self,tw,tf,b,h):
        poly = [(b/2,0),(b/2,-tf),(tw/2,-tf),(tw/2,-h),(-tw/2,-h),(-tw/2,-tf),(-b/2,-tf),(-b/2,0)]
        self.tw = tw
        self.tf = tf
        self.bw = b
        self.h = h
        self.poly = poly
        self.name = "Viga T"
        pass
        

class Seccion_Viga():
    def __init__(self,Viga,Ref,stirrup,recover=4): ##Viga T, Viga rectangular
        #self.type = Type
        self.viga = Viga
        #self.fc = Viga.fc
        #self.fy = Viga.fy
        #self.Es = Viga.Es
        #self.diams = steels #Starting from the tension zone
        #self.s = spacing
        #self.n_s = len(self.As)
        #self.poly = Poly
        self.ref = Ref
        self.strp = stirrup
        self.rec = recover
        self.n_s = None
        self.As = None
        self.ds_t = None
        self.As_t = None
        self.ds_c = None
        self.As_c = None
        self.As_plot_t = None
        self.As_plot_c = []
        self.As_plot = None
        self.steels_t = None
        self.steels_c = None
        self.steels = None
        self.ds = None
        self.section = None
        self.Asmin = None
        self.As_tot = None
        

    def Steel_distribution_t(self,steels,spacing):
        steels.reverse()
        self.steels_t = steels
        ds = []
        As = []
        for i in range(len(steels)):
            Asi = 0
            #self.As_plot_t.append()ss
            if i==0:
                num = 0
                for bar in steels[0]:
                    di = self.rec + diam_steels[self.strp] + diam_steels[bar]/2
                    Asi = Asi + As_steels[bar] 
                    num = num + As_steels[bar]*di
                d_s = num/Asi
                #print(steels.index(capa))
            else:
                d_s = ds[i-1] + spacing
                for bar in steels[i]:
                    Asi = Asi + As_steels[bar]
                #print(steels.index(capa))
            ds.append(d_s)
            As.append(Asi)

        '''d_base = self.rec + diam_steels[self.strp]
        for capa in steels:
            num = 0
            den = 0
            Asi = 0
            d_avg = 0
            count = 0
            for bar in capa:
                di = d_base + diam_steels[bar]/2
                Asi = Asi + As_steels[bar] 
                num = num + As_steels[bar]*di
                den = den + As_steels[bar]
                d_avg = d_avg + diam_steels[bar]/2
                count +=1
            ds.append(num/den)
            As.append(Asi)
            d_avg = d_avg/count
            d_base = d_base + d_avg + spacing'''
        #print(ds)
        #print(As)
        As.reverse()
        ds.reverse()
        self.As_t = As
        self.ds_t = ds
        self.n_s = len(As)
        temporal = []
        for i in range(len(steels)):
            as_plot = []
            for bar in steels[i]:
                as_plot.append(As_steels[bar])
            temporal.append(as_plot)
        self.As_plot_t = temporal[::-1]

    def Steel_distribution_c(self,steels):
        self.steels_c = steels
        Asi = 0
        num = 0
        for bar in steels:
            di = self.rec + diam_steels[self.strp] + diam_steels[bar]/2
            Asi = Asi + As_steels[bar] 
            num = num + As_steels[bar]*di
        self.ds_c = num/Asi
        self.As_c = Asi

        as_plot = []
        for bar in steels:
            as_plot.append(As_steels[bar])
        self.As_plot_c.append(as_plot)

    def Create_section(self):
        poly = self.viga.poly
        
        ds = []
        As = []
    
        if self.ds_c != None:
            ds.append(self.ds_c)
            As.append(self.As_c)
        for i in range(self.n_s):
            ds.append(self.viga.h - self.ds_t[i])
            As.append(self.As_t[i])
        #ds.append(self.ds_t.reverse())
        self.ds = ds
        self.As = As
        #self.ds.reverse()
        #self.As.reverse()
        beam_section = Sections(self.viga.fc,self.viga.fy,self.viga.Es,self.As,self.ds,poly,self.ref)
        self.section = beam_section
        self.As_plot = self.As_plot_c + self.As_plot_t
        self.steels = [self.steels_c] + self.steels_t[::-1]
        
    #def T_section(self,)

    def Find_c(self):
        final_section = copy.deepcopy(self.section)
        #print(final_section)
        #print(final_section.As)
        final_section.Comp_defo(0.1)
        for c in np.arange(0.2,self.viga.h,0.1):
            self.section.Comp_defo(c)
            #print(f"Pn of final section:{final_section.Pn}")
            #print(f"Pn of current section:{self.section.Pn}")
            if abs(self.section.Pn)<abs(final_section.Pn):
                final_section=copy.deepcopy(self.section)
                #print("Change")

        self.section = final_section
        self.section.d_dis(self.section.c)

        ##EN TEORÍA YA ESTÁ, PROBAR CON EJEMPLO PARA CORROBORAR Pn y Mn

    def Check_lims_ACI(self):
        print("Verificación de acero mínimo:")
        lim_1 = (0.8*(self.viga.fc)**0.5*self.viga.bw*self.section.d)/self.viga.fy
        print(f"(a) {lim_1}")
        lim_2 = (14*self.viga.bw*self.section.d)/self.viga.fy
        print(f"(b) {lim_2}")
        if(lim_1>=lim_2):
            Asmin = lim_1
        else:
            Asmin = lim_2

        if(sum(self.As)>Asmin):
            print(f"{sum(self.As)}>{Asmin} CUMPLE")
        else:
            print(f"{sum(self.As)}>{Asmin} No cumple")

        print("Verificación de et minimo(acero máximo):")

        if(self.section.et>=0.004):
            print(f"{self.section.et}>0.004 CUMPLE")
        else:
            print(f"{self.section.et}<0.004 No cumple")

    
    def Asmin_E060(self):
        Asmin = 0.7*((self.section.fc**0.5)/self.section.fy)*self.viga.bw*self.viga.h
        As_tot = sum(self.As)
        self.Asmin = Asmin
        self.As_tot = As_tot

    def Plot_rec_beam(self,path):
        import matplotlib.pyplot as plt
        from shapely import Polygon, LineString, intersection
        from shapely.ops import split
        import numpy as np
        import matplotlib.patches as ptch
        import matplotlib

        section = Polygon(self.section.poly)
        x, y = section.exterior.xy
        fig,ax = plt.subplots()
        ax.plot(x, y, color='#a7ada0')  # Plot the exterior of the polygon
        ax.fill(x, y, color='#8b8f86', alpha=0.5)

        #line = LineString([(x_min,-self.section.a),(x_max,-self.section.a)])  #Crear la línea más "larga" para splitear la seccion luego

        #zeros = [0]*self.section.n_s
        ds_array = -1*np.array(self.section.ds)
        #plt.scatter(zeros,ds_array)

        d_strp = diam_steels[self.strp]

        #print(self.steels)
        ## Aceros
        for i in range(len(self.As_plot)):
            if(len(self.As_plot[i])==1):
                s = 0
                xo = 0
            else:
                s = (self.viga.bw - 2*self.rec - 2*diam_steels[self.strp] - diam_steels[self.steels[i][0]]/2 - diam_steels[self.steels[i][-1]]/2)/(len(self.As_plot[i])-1)
                xo = -self.viga.bw/2 + self.rec + diam_steels[self.strp] + diam_steels[self.steels[i][0]]/2
            for j in range(len(self.As_plot[i])):
                xpos = xo + j*s #+ diam_steels[self.steels[i][j]]/2
                bar = ptch.Circle((xpos, ds_array[i]),radius=diam_steels[self.steels[i][j]]/2,color="#444740")
                #print(f"{i}{j}")
                ax.add_patch(bar)
                #plt.scatter(xpos, ds_array[i])
                plt.annotate(f'{self.steels[i][j]}"',(xpos+diam_steels[self.steels[i][j]]/2,ds_array[i]+diam_steels[self.steels[i][j]]/2))
            #plt.annotate(f"{str(round(a_s,2))}cm2", (zeros[i],ds_array[i]))
        ax.set_aspect('equal')

        ##Estribo
        b = self.viga.bw
        h = self.viga.h
        rec = self.rec
        #[(b/2,0),(b/2,-h),(-b/2,-h),(-b/2,0)]
        stirrup = matplotlib.lines.Line2D([b/2-rec-d_strp,b/2-rec-d_strp,-b/2+rec+d_strp,-b/2+rec+d_strp,b/2-rec-d_strp],[-rec-d_strp,-h+rec+d_strp,-h+rec+d_strp,-rec-d_strp,-rec-d_strp],linewidth = d_strp,color="#444740")
        #ax.plot([b/2-rec,b/2-rec,-b/2+rec,-b/2+rec,b/2-rec],[-rec,-h+rec,-h+rec,-rec,-rec])
        ax.add_line(stirrup)
        plt.axis('off')
        self.fig = fig  
        try:
            plt.savefig(f"{path}/Beam Section")
        except:
            print("No figure is defined")


    def Plot_T_beam(self):
        import matplotlib.pyplot as plt
        from shapely import Polygon, LineString, intersection
        from shapely.ops import split
        import numpy as np
        import matplotlib.patches as ptch
        import matplotlib

        section = Polygon(self.section.poly)
        x, y = section.exterior.xy
        fig,ax = plt.subplots()
        ax.plot(x, y, color='#a7ada0')  # Plot the exterior of the polygon
        ax.fill(x, y, color='#8b8f86', alpha=0.5)

        #line = LineString([(x_min,-self.section.a),(x_max,-self.section.a)])  #Crear la línea más "larga" para splitear la seccion luego

        #zeros = [0]*self.section.n_s
        ds_array = -1*np.array(self.section.ds)
        #plt.scatter(zeros,ds_array)

        d_strp = diam_steels[self.strp]

        #print(self.steels)
        ## Aceros
        for i in range(len(self.As_plot)):
            if(len(self.As_plot[i])==1):
                s = 0
                xo = 0
            else:
                s = (self.viga.tw - 2*self.rec - 2*diam_steels[self.strp] - diam_steels[self.steels[i][0]]/2 - diam_steels[self.steels[i][-1]]/2)/(len(self.As_plot[i])-1)
                xo = -self.viga.tw/2 + self.rec + diam_steels[self.strp] + diam_steels[self.steels[i][0]]/2
            for j in range(len(self.As_plot[i])):
                xpos = xo + j*s #+ diam_steels[self.steels[i][j]]/2
                bar = ptch.Circle((xpos, ds_array[i]),radius=diam_steels[self.steels[i][j]]/2,color="#444740")
                #print(f"{i}{j}")
                ax.add_patch(bar)
                #plt.scatter(xpos, ds_array[i])
                plt.annotate(f'{self.steels[i][j]}"',(xpos+diam_steels[self.steels[i][j]]/2,ds_array[i]+diam_steels[self.steels[i][j]]/2))
            #plt.annotate(f"{str(round(a_s,2))}cm2", (zeros[i],ds_array[i]))
        ax.set_aspect('equal')

        ##Estribo
        tw = self.viga.tw
        h = self.viga.h
        rec = self.rec
        #[(b/2,0),(b/2,-h),(-b/2,-h),(-b/2,0)]
        stirrup = matplotlib.lines.Line2D([tw/2-rec-d_strp,tw/2-rec-d_strp,-tw/2+rec+d_strp,-tw/2+rec+d_strp,tw/2-rec-d_strp],[-rec-d_strp,-h+rec+d_strp,-h+rec+d_strp,-rec-d_strp,-rec-d_strp],linewidth = d_strp,color="#444740")
        #ax.plot([b/2-rec,b/2-rec,-b/2+rec,-b/2+rec,b/2-rec],[-rec,-h+rec,-h+rec,-rec,-rec])
        ax.add_line(stirrup)

        self.fig = fig  
        try:
            plt.savefig("Beam Section")
        except:
            print("No figure is defined")


    def Make_report(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(
            loader=FileSystemLoader('C:/Users/EDSON/OneDrive - UNIVERSIDAD NACIONAL DE INGENIERIA/Cursos/Automatización del Análisis y Diseño estructural/Sesión 3'),  ##This will set the "relative directory" as '??' in the next statements
        )

        import os

        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        print("Current script directory:", current_script_directory)

        template = env.get_template('./template_beam_section.tex') 
        with open('../report_beam_section.tex', 'w') as f:
            f.write(template.render(name=self.viga.name))