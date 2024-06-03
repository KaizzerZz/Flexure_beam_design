def Comp_defo(fc,fy,Es,A_s,d_s,c,poly,ref):
    from Packages.CP import Cent_plas
    from shapely import Polygon, LineString, intersection
    from shapely.ops import split
    import matplotlib.pyplot as plt
    import numpy as np


    #Getting the witney area
    c = 18 # cm
    if(175<=fc<=280):
        β1 = 0.85
    elif(280<fc<550):
        β1 = 0.85-0.05*(fc-280)/70
    elif(fc>=550):
        β1 = 0.65

    a = β1*c
    print(a)

    section = Polygon(poly)
    x, y = section.exterior.xy
    plt.figure()
    plt.plot(x, y, color='blue')  # Plot the exterior of the polygon
    plt.fill(x, y, color='lightblue', alpha=0.5)

    x_s = []
    for coord in poly:
        x_s.append(coord[0])
    x_min = min(x_s)
    x_max = max(x_s)

    line = LineString([(x_min,-a),(x_max,-a)])

    witney_sec = split(section,line).geoms[0]
    x,y = witney_sec.exterior.xy
    plt.plot(x,y,color='gray')
    plt.fill(x, y, color='black', alpha=0.5)

    line_c = intersection(section,line)
    x,y = line_c.xy
    plt.plot(x,y,color='green')

    Ac = section.area
    cen_c = section.centroid.y
    print(cen_c)

    Aw = witney_sec.area
    cen_w = witney_sec.centroid.y

    #Some params

    n_s = len(d_s)
    dt = d_s[-1]

    et = abs(0.003*(c-dt)/c)
    ey = fy/Es

    #Reduction factor
    if(ref=="Espirales"):
        a = 0.75
        b = 0.15
    elif(ref=="Otro"):
        a = 0.65
        b = 0.25

    if(et<ey):
        fi = a
    elif(ey<et<0.005):
        fi =  a + b*(et-ey)/(0.005-ey)
    elif(et>=0.005):
        fi = 0.9
    
    #Calcs

    Cc = 0.85*fc*Aw/1000

    CP = round(Cent_plas(fc,fy,Ac,cen_c,n_s,A_s,d_s),1)

    Pn = Cc
    Mn = Cc*(CP-cen_w)

    for i in range(n_s):
        es = round(0.003*(c-d_s[i])/c,4)
        print(f"es{str(i+1)}=0.003({str(c)}-{str(d_s[i])})/{str(c)}={str(es)}")
        if(abs(es)<ey):
            fs = Es*es
            print(f"{str(es)}<{str(ey)}")
        elif(abs(es)>=ey):
            fs = np.sign(es)*fy
            print(f"{str(es)}>={str(ey)}")
        print(f"fs{str(i+1)}={str(round(fs,2))}")
        Fs = fs*A_s[i]/1000
        print(f"Fs{str(i+1)}={str(Fs)}")

        Pn = Pn + Fs
        Mn = Mn + Fs*(CP-d_s[i])

    print(Pn)
    print(Mn)
    return et