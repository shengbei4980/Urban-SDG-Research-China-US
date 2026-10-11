"""Reproduce the approved two-panel figure from frozen project-family allocations.

One point per administrative location; all 478 locations are retained.
F: domestic supply share. D: own-SDG-weighted JSD vs other domestic locations.
OLS on log10 supply and its pointwise 95% mean-response CI are descriptive overlays.
"""
from pathlib import Path
import hashlib
import json
import platform
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
from scipy.special import rel_entr
from scipy.stats import linregress, t as student_t

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/input_snapshots'
DATA, FIG, QA = ROOT/'data', ROOT/'figures', ROOT/'review/marker_revision'
TASKS = [f'K{i:02d}' for i in range(1, 7)]
KEYS = ['agency', 'unit_id']
THRESHOLD = 20






def plot(u,palette,errors):
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':7,'axes.labelsize':7.5,'xtick.labelsize':6.5,'ytick.labelsize':6.5,
        'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':0.75,
        'axes.edgecolor':'#000000','text.color':'#202830','axes.labelcolor':'#202830',
        'legend.frameon':False,'savefig.facecolor':'white'})
    # Quantitative grid: matched panels at 183 mm full-figure width.
    fig=plt.figure(figsize=(7.2047244094,4.20),facecolor='white')
    fig.text(.025,.96,'b',fontsize=12,fontweight='bold',va='top')
    fig.text(.095,.958,'Research supply and task-profile differentiation',fontsize=10.2,fontweight='bold',va='top')
    fig.text(.095,.918,'All research locations · 12 SDGs · six knowledge tasks',fontsize=7.5,color='#56616B',va='top')
    axes=[]; annotations=[]; panel_report=[]; regressions=[]; regression_curves=[]
    xmin,xmax=.004,32
    for ix,(agency,title,marker) in enumerate([('NSF','United States · NSF','o'),('NSFC','China · NSFC','s')]):
        ax=fig.add_axes([.10+ix*.455,.265,.395,.395*7.2047244094/4.20/1.35])
        ax.set_box_aspect(1/1.35)
        axes.append(ax)
        z=u[u.agency.eq(agency)].copy()
        dark,mid=palette[agency+'_DARK'],palette[agency+'_MID']
        ax.set_xscale('log');ax.set_xlim(xmin,xmax);ax.set_ylim(-.22,.94)
        ticks=[.01,.1,1,10]
        ax.xaxis.set_major_locator(FixedLocator(ticks));ax.xaxis.set_minor_locator(NullLocator())
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'))
        ax.set_yticks([-.2,0,.2,.4,.6,.8]);ax.set_axisbelow(True)
        ax.grid(color='#E1E4E8',linewidth=.45)
        ax.tick_params(direction='out',width=.65,length=3,color='#000000',pad=3)
        for spine in ax.spines.values():
            spine.set_visible(True);spine.set_color('#000000');spine.set_linewidth(.75)
        xmed,ymed=z.F_pct.median(),z.jsd_rest_bits.median()
        ax.axvline(xmed,color='#92999F',linewidth=.7,ls=(0,(3,3)),zorder=1)
        ax.axhline(ymed,color='#92999F',linewidth=.7,ls=(0,(3,3)),zorder=1)
        # User-requested ordinary least squares; use all locations and no extrapolation.
        x=np.log10(z.F_pct.to_numpy()); y=z.jsd_rest_bits.to_numpy(); n=len(x)
        fit=linregress(x,y)
        xgrid=np.linspace(x.min(),x.max(),200)
        ygrid=fit.intercept+fit.slope*xgrid
        residual=y-(fit.intercept+fit.slope*x)
        mse=float(np.dot(residual,residual)/(n-2))
        sxx=float(np.dot(x-x.mean(),x-x.mean()))
        se_mean=np.sqrt(mse*(1/n+(xgrid-x.mean())**2/sxx))
        tcrit=student_t.ppf(.975,n-2)
        lower,upper=ygrid-tcrit*se_mean,ygrid+tcrit*se_mean
        assert lower.min()>-.22 and upper.max()<.94
        ax.fill_between(10**xgrid,lower,upper,color=mid,alpha=.23,lw=0,zorder=1.2)
        ax.plot(10**xgrid,ygrid,color=dark,lw=1.15,zorder=2.5)
        ax.text(.035,.035,f'Pearson r = {fit.rvalue:.3f}  |  P < 0.001\nOLS on log10 supply; n = {n}',
            transform=ax.transAxes,fontsize=6.2,color=dark,va='bottom',ha='left',zorder=6,
            bbox=dict(facecolor='white',edgecolor='none',pad=1.2))
        assert fit.pvalue<.001
        regressions.append(dict(agency=agency,n_locations=n,x='log10(F_pct)',y='jsd_rest_bits',
            slope=fit.slope,intercept=fit.intercept,pearson_r=fit.rvalue,p_value=fit.pvalue,
            slope_se=fit.stderr,slope_ci_low=fit.slope-tcrit*fit.stderr,slope_ci_high=fit.slope+tcrit*fit.stderr,
            residual_df=n-2,residual_variance=mse,confidence_level=.95,
            band='pointwise mean-response Student-t CI; not a prediction interval',
            fit_scope='all observed locations; no support filtering; no extrapolation',
            limitation='unadjusted descriptive OLS; shared reference and finite-support bias not calibrated'))
        regression_curves.append(pd.DataFrame(dict(agency=agency,F_pct=10**xgrid,
            log10_F_pct=xgrid,fitted_jsd=ygrid,mean_ci_low=lower,mean_ci_high=upper)))
        groups=[(False,'none',.58),(True,mid,.68)]
        plotted=0
        for supported,face,lw in groups:
            s=z[z.marker_filled.eq(supported)]
            points=ax.scatter(s.F_pct,s.jsd_rest_bits,s=12,marker=marker,
                facecolors=face,edgecolors=dark,linewidths=lw,alpha=1,zorder=3)
            points.set_gid(f'{agency}_{"filled" if supported else "open"}_{len(s)}_locations')
            plotted+=len(points.get_offsets())
        assert plotted==len(z)
        subtitle='352 counties and equivalents' if agency=='NSF' else '126 prefecture-level units'
        ax.text(0,1.105,title,transform=ax.transAxes,color=dark,fontsize=9.5,fontweight='bold',va='bottom')
        ax.text(0,1.035,subtitle,transform=ax.transAxes,fontsize=7,color='#56616B',va='bottom')
        ax.set_xlabel('National sample supply (%) · log scale',labelpad=7)
        if ix==0:
            ax.set_ylabel('SDG-conditioned task-profile divergence (bits)',labelpad=6)
        # A compact ranked list avoids long leaders to near-coincident top-five points.
        labeled=z[z.direct_label].sort_values('supply_rank')
        ax.text(.50,.935,'Leading locations',transform=ax.transAxes,fontsize=6.2,
                color='#56616B',fontweight='bold',ha='left',va='center')
        ax.text(.975,.935,'Share',transform=ax.transAxes,fontsize=6.2,
                color='#56616B',fontweight='bold',ha='right',va='center')
        ax.plot([.50,.975],[.905,.905],transform=ax.transAxes,color='#CFD4D9',lw=.55,zorder=2)
        for (_,r),ty in zip(labeled.iterrows(),[.855,.775,.695,.615,.535]):
            ann=ax.text(.50,ty,r.label,transform=ax.transAxes,ha='left',va='center',fontsize=6,
                color=dark,zorder=5)
            ann.set_gid(f'label_{r.unit_id}')
            annotations.append((ax,ann))
            value=ax.text(.975,ty,f'{r.F_pct:.2f}%',transform=ax.transAxes,ha='right',va='center',
                fontsize=6,color=dark,zorder=5)
            annotations.append((ax,value))
        ax.text(0,-.205,f'{int(z.marker_filled.sum())} filled · {int((~z.marker_filled).sum())} open',
            transform=ax.transAxes,fontsize=6.5,color='#56616B')
        panel_report.append(dict(agency=agency,locations=len(z),filled=int(z.marker_filled.sum()),
            open=int((~z.marker_filled).sum()),median_supply_pct=float(xmed),median_jsd_bits=float(ymed),
            x_limits=[xmin,xmax],y_limits=[-.22,.94],labels=labeled.label.tolist()))
    handles=[Line2D([],[],marker='o',mfc='none',mec='#424B52',lw=0,ms=4,label='<20 project families'),
        Line2D([],[],marker='o',mfc='#9EA8B0',mec='#424B52',lw=0,ms=4,label='≥20 project families'),
        Line2D([],[],color='#92999F',lw=.7,ls=(0,(3,3)),label='Within-country medians'),
        Line2D([],[],color='#424B52',lw=1.15,label='OLS fit on log10 supply'),
        Patch(facecolor='#9EA8B0',alpha=.23,edgecolor='none',label='95% CI for fitted mean')]
    fig.legend(handles=handles,loc='center',bbox_to_anchor=(.53,.117),ncol=3,fontsize=6.3,
        handletextpad=.55,columnspacing=1.6)
    fig.text(.10,.070,'Each point is one location; all 478 are retained. In-panel lists show the five largest suppliers and their shares.',fontsize=6.1,color='#56616B')
    fig.text(.10,.043,'Fits are descriptive and unconstrained; differences in project support can affect the observed association.',fontsize=6.1,color='#56616B')
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    boxes=[ann.get_window_extent(renderer) for _,ann in annotations]
    label_overlaps=[(i,j) for i in range(len(boxes)) for j in range(i+1,len(boxes)) if boxes[i].overlaps(boxes[j])]
    outside=[i for i,((ax,ann),box) in enumerate(zip(annotations,boxes))
             if box.x0<ax.bbox.x0 or box.x1>ax.bbox.x1 or box.y0<ax.bbox.y0 or box.y1>ax.bbox.y1]
    assert not label_overlaps, label_overlaps
    assert not outside, outside
    points_beneath_labels=[]
    for i,((ax,ann),box) in enumerate(zip(annotations,boxes)):
        for collection in ax.collections:
            pixels=ax.transData.transform(collection.get_offsets())
            if any(box.expanded(1.03,1.12).contains(x,y) for x,y in pixels):
                points_beneath_labels.append(i)
    assert not points_beneath_labels,points_beneath_labels
    assert all(all(s.get_visible() and s.get_edgecolor()==(0.,0.,0.,1.) for s in ax.spines.values()) for ax in axes)
    marker_checks=[]
    for ax in axes:
        assert np.isclose(ax.bbox.width/ax.bbox.height,1.35)
        for collection in ax.collections:
            if not (collection.get_gid() or '').endswith('_locations'): continue
            path=collection.get_paths()[0].get_extents()
            for transform in collection.get_transforms():
                width=path.width*abs(transform[0,0]); height=path.height*abs(transform[1,1])
                assert np.isclose(width/height,1,atol=1e-10)
            marker_checks.append({'id':collection.get_gid(),'width_over_height':float(width/height),'points':len(collection.get_offsets())})
    (QA/'marker_aspect_verification.json').write_text(json.dumps(marker_checks,indent=2),encoding='utf-8')
    name='Figure3b_NSF_NSFC_all_locations_two_panels'
    fig.savefig(FIG/(name+'.pdf'))
    fig.savefig(FIG/(name+'.svg'))
    fig.savefig(FIG/(name+'.png'),dpi=600)
    fig.savefig(FIG/(name+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(FIG/'Figure3b_preview.png',dpi=300)
    plt.close(fig)
    report=dict(status='PASS',locations=478,no_locations_removed=True,panels=panel_report,
        numeric_comparison_max_error=errors,black_full_frames=True,label_overlap_count=len(label_overlaps),
        labels_outside_axes=outside,points_beneath_labels=points_beneath_labels,
        figure_size_mm=[183,106.68],raster_dpi=600,palette=palette,
        point_alpha=1,filled_marker_area_pt2=12,open_marker_area_pt2=12,
        regression='OLS: JSD = intercept + slope × log10(F_pct), separately by country',
        confidence_intervals='pointwise 95% Student-t mean-response confidence bands',
        independence='one administrative location per point; profiles share domestic reference data',
        versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__))
    (QA/'data_and_figure_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(regressions).to_csv(QA/'linear_regression_statistics.csv',index=False,encoding='utf-8-sig')
    pd.concat(regression_curves,ignore_index=True).to_csv(QA/'regression_curves_95CI.csv',index=False,encoding='utf-8-sig')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    for folder in (FIG,QA): folder.mkdir(parents=True,exist_ok=True)
    locations=pd.read_csv(DATA/'Figure3b_full_478_locations.csv')
    colors=json.loads((DATA/'Figure1a_referenced_palette.json').read_text(encoding='utf-8-sig'))
    assert locations.groupby('agency').size().to_dict()=={'NSF':352,'NSFC':126}
    plot(locations,colors,{'source':'unchanged frozen location table'})
