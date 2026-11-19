"""Rebuild inspection tables and figure from the original synthetic course CSV."""
from pathlib import Path
import hashlib,json,sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'
def main():
    OUT.mkdir(exist_ok=True)
    path=ROOT/'data/waze_dataset.csv'
    raw=pd.read_csv(path);df=raw.copy()
    for name,num,den in [('km_per_drive','driven_km_drives','drives'),('km_per_driving_day','driven_km_drives','driving_days'),('drives_per_driving_day','drives','driving_days')]:
        df[name]=df[num]/df[den].replace(0,np.nan)
    assert raw.ID.is_unique
    assert not np.isinf(df.select_dtypes('number').to_numpy()).any()
    pd.DataFrame({'dtype':raw.dtypes.astype(str),'non_null':raw.notna().sum(),'missing':raw.isna().sum(),'missing_pct':raw.isna().mean()*100}).to_csv(OUT/'column_summary.csv')
    raw.describe().T.to_csv(OUT/'descriptive_statistics.csv')
    raw.groupby(raw.label.isna()).describe().to_csv(OUT/'missing_label_comparison.csv')
    counts=raw.label.value_counts()
    pd.DataFrame({'users':counts,'pct_known_labels':counts/counts.sum()*100}).to_csv(OUT/'known_label_distribution.csv')
    df.groupby('label').median(numeric_only=True).drop(columns='ID').to_csv(OUT/'group_medians.csv')
    df.groupby('label')[['km_per_drive','km_per_driving_day','drives_per_driving_day']].agg(['count','median']).to_csv(OUT/'ratio_coverage.csv')
    (pd.crosstab(df.device,df.label,normalize='index')*100).to_csv(OUT/'device_rates.csv')
    checks={'rows':len(raw),'columns':raw.shape[1],'duplicate_rows':int(raw.duplicated().sum()),'duplicate_ids':int(raw.ID.duplicated().sum()),'missing_labels':int(raw.label.isna().sum()),'zero_drives_positive_km':int(((raw.drives==0)&(raw.driven_km_drives>0)).sum()),'zero_driving_days_positive_km':int(((raw.driving_days==0)&(raw.driven_km_drives>0)).sum()),'raw_csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'python':sys.version.split()[0],'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__}
    (OUT/'validation.json').write_text(json.dumps(checks,indent=2)+'\n')
    med=raw.groupby('label')[['activity_days','driving_days']].median()
    fig,ax=plt.subplots(figsize=(9,4.6),layout='constrained');x=np.arange(2);w=.32
    for i,(group,color,title) in enumerate([('churned','#B34B36','Churned'),('retained','#23788C','Retained')]):
        bars=ax.bar(x+(i-.5)*w,med.loc[group],w,color=color,label=title)
        ax.bar_label(bars,fmt='%.0f',padding=4,fontsize=12)
    ax.set(xticks=x,xticklabels=['App activity days','Driving days'],ylabel='Median days in month',ylim=(0,21))
    ax.set_title('Churned users were active on fewer days',loc='left',fontsize=16,pad=18)
    ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.15)
    fig.text(.01,-.05,'Synthetic course data · Known labels: 2,536 churned; 11,763 retained · Descriptive association',fontsize=9)
    fig.savefig(OUT/'activity_days.png',dpi=160,bbox_inches='tight');plt.close(fig)
    print(f'Generated inspection outputs for {len(raw):,} users.')
if __name__=='__main__':main()
