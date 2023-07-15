from django.shortcuts import render,redirect
from django.http import FileResponse,HttpResponse
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime    # Python 標準
import numpy as np
import openpyxl
import seaborn as sns
import glob,shutil
import os
from django.conf import settings
import tempfile

def upload_file(request):
    import pandas as pd
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')

        print(files)
        
        #カレントディレクトリに含まれるファイル、フォルダを取得
        #files = glob.glob('*.xlsx')
        #カレントディレクトリに含まれるファイル、フォルダの内容
        #バグを防ぐために'集計.xlsx'を除く files.remove('集計.xlsx')
        files = [file for file in files if str(file).endswith('.xlsx')]
        files = [file for file in files if str(file) != '集計.xlsx']
        print(files)
        #filesの中に含まれる名前を表示
        files_except_name = [str(s).replace('.xlsx', '') for s in files]
        print(files_except_name)
        #----------------------------------------
        # データ読込
        #----------------------------------------
        # xlsxから必要な部分のみdfとして読込

        #それぞれのファイルから要素を読み込んできて、縦に結合する

        sum = 0

        for i in range(len(files)):
            df_files = pd.read_excel(files[i], sheet_name=0, header=0)
            if sum == 0 :
                df_all = df_files
                sum = sum + 1
            else:
                df_all = pd.concat([df_all, df_files], axis=0,ignore_index = True)


        print(df_all)
        #全体の大きさ確認用
        df_all.shape


        #保険としてリストをコピー
        df_list = df_all
        #列のindexを表示
        df_list.columns
        #必要な部分以外を全部切り落とす
        df_list_cut = df_list.drop(['工数番号', '作業計上日', '事業部ｺｰﾄﾞ', '事業部名称', '部門ｺｰﾄﾞ', '部門略称',
        '所属部門ｺｰﾄﾞ', '所属部門名称',  '社内指示番号', '社内指示行番号', '製番',
        '製番状態', 'ﾘｽﾄ番号', '作業区分', '作業内容名称', '作業稼動開始時間', '作業稼動終了時間','作業時間', '作業単価', '作業金額', '作業理由ｺｰﾄﾞ', '作業理由名称',
        '作業原価科目ｺｰﾄﾞ', '作業原価科目名称', '資源区分', '資源ｺｰﾄﾞ', '資源名称', '資源稼動開始時間',
        '資源稼動終了時間', '資源時間', '資源単価', '資源金額', '資源理由ｺｰﾄﾞ', '資源理由名称', '資源原価科目ｺｰﾄﾞ',
        '資源原価科目名称', '備考', '登録ID', '登録日時', '更新ID', '更新日時'],axis=1)
        print(df_list_cut)

        #作業日の日の表示方法をdatatimeに変更
        df_list_cut['作業日'] = pd.to_datetime(df_list_cut['作業日'])

        # 年度と月の列を追加
        df_list_cut['年度'] = df_list_cut['作業日'].dt.year
        df_list_cut['月'] = df_list_cut['作業日'].dt.month

        # 年度と月でソート
        df_list_cut = df_list_cut.sort_values(['年度', '月'])

        # 年度ごとにデータを分割する
        dfs = []
        for year in range(2022, 2025):#とりあえず2025年まで
            year_data = df_list_cut[df_list_cut['年度'] == year].copy()
            dfs.append(year_data)

        #月ごとにデータを分割する
        for i, year_data in enumerate(dfs):
            year_month_dfs = []
            for month in range(1, 13):

                month_data = year_data[year_data['月'] == month].copy()
                year_month_dfs.append(month_data)
            dfs[i] = year_month_dfs


        print(dfs)

        import pandas as pd
        #月ごとに分割したデータを修正して格納する、最終結果のリストを作成
        result_dfs = []

        #月ごとのデータに、直接工数などの項目を計算して追加し修正する
        for year, year_month_dfs in zip(range(2022, 2024), dfs):
            for month, month_data in zip(range(1, 13), year_month_dfs):
                if month_data.empty:
                    continue
                # データフレームをコピー
                df_modified = month_data.copy()

                # データの修正と計算
                df_modified['作業内容ｺｰﾄﾞ'] = df_modified['作業内容ｺｰﾄﾞ'].astype(str)
                df_modified['作業内容ｺｰﾄﾞ_頭文字'] = df_modified['作業内容ｺｰﾄﾞ'].str[0]

                # 合計時間の計算
                df_sum = df_modified.groupby(['担当者ｺｰﾄﾞ', '担当者略称']).agg({'作業時間(時間単位)': 'sum'}).reset_index()

                # Dから始まる作業の合計時間の計算
                df_sum_d = df_modified[df_modified['作業内容ｺｰﾄﾞ_頭文字'] == 'D'].groupby(['担当者ｺｰﾄﾞ', '担当者略称']).agg({'作業時間(時間単位)': 'sum'}).reset_index()
                df_sum_d = df_sum_d.rename(columns={'作業時間(時間単位)': '直接工数'})

                # D以外の作業の合計時間の計算＆df_sum_not_dにいろいろな項目を追加
                df_sum_not_d = df_sum.merge(df_sum_d, on=[ '担当者ｺｰﾄﾞ', '担当者略称'], how='left')
                df_sum_not_d['直接工数'] = df_sum_not_d['直接工数'].fillna(0)
                df_sum_not_d['関接工数'] = df_sum_not_d['作業時間(時間単位)'] - df_sum_not_d['直接工数']
                #（関節率の計算）
                df_sum_not_d['関接率'] =round(df_sum_not_d['関接工数']/ df_sum_not_d['作業時間(時間単位)']*100,1 )

                # 月ごとのデータフレームを結果として先頭に追加
                df_sum_not_d.insert(0,'月',month)
                df_sum_not_d.insert(0,'年度',year)
                result_dfs.append(df_sum_not_d)

        # 結果を表示
        for df_result in result_dfs:
            print(df_result)

        #分割したデータを結合し、1つのデータフレームにする
        sum = 0

        for df_result in result_dfs:
            df_files = df_result
            if sum == 0 :
                final_result = df_files
                sum = sum + 1
            else:
                final_result = pd.concat([final_result, df_files], axis=0,ignore_index = True)


        print(final_result)
        #excelに貼り付け♪
        final_result.to_excel("/Users/takas/Desktop/230208_工数分析/集計.xlsx")
        #excelに貼り付け♪
        output_path = os.path.join(settings.MEDIA_ROOT, '集計.xlsx')
        final_result.to_excel(output_path, index=False)

        if os.path.exists(output_path):
            with open(output_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="集計.xlsx"'
                print("uuu")
                return response
        else:
            return HttpResponse("ファイルが見つかりません")
    else:
        return render(request,"syuukei/upload.html")
