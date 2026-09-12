# f(m) = number of PLRRs whose first generated value a_{k+1} = m
# = sum over k>=1 of sum over compositions m=t_1+..+t_k of prod d(t_i)
M=40
d=[0]*(M+1)
for i in range(1,M+1):
    for j in range(i,M+1,i): d[j]+=1
# f = [x^m] D/(1-D) ; equivalently f(m) = d(m) + sum_{t=1}^{m-1} d(t)*f(m-t)
f=[0]*(M+1)
for m in range(1,M+1):
    f[m]=d[m]+sum(d[t]*f[m-t] for t in range(1,m))
cum=0
for m in range(1,M+1):
    cum+=f[m]
    print(m, d[m], f[m], cum)
