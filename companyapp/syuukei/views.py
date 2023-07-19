from django.shortcuts import render,redirect
from django.http import HttpResponse
import os
from django.conf import settings
import logging




def upload_file(request):
    import pandas as pd
    logger = logging.getLogger('django')  # Get the logger with the 'django' name specified in LOGGING settings
    if request.method == 'POST' and request.FILES.getlist('files'):
        try:

            files = request.FILES.getlist('files')


            print(files)
            #logger.info("Before reading files.")
            #for file in files:
                #logger.info(file.name)


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
                logger.info(f"Reading file: {files[i].name}")
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

            # Keep only the desired columns in df_list
            df_list_cut = df_list[['作業日', '担当者ｺｰﾄﾞ', '担当者略称', '作業内容ｺｰﾄﾞ', '作業時間(時間単位)']]
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
            #logger.info("Before writing to Excel.")
            #logger.info(final_result)
            
            df_list_cut_two =  df_list[["製番", '作業時間(時間単位)']]
            # 製番 の頭文字がKT　のものを削除する。
            df_seibann = df_list_cut_two[~df_list_cut_two['製番'].str.startswith('KT')]

            # 製番の型の名前をリストを作成する。
            seibann_name = df_seibann['製番'].unique()

            # 新しいデータフレームを作成する。
            result_df = pd.DataFrame(columns=['製番名', '合計時間'])

            # それぞれの製番ごとの作業時間の合計時間を求める。それをresult_dfにする。
            for name in seibann_name:
                total_time = df_seibann[df_seibann['製番'] == name]['作業時間(時間単位)'].sum()
                result_df = pd.concat([result_df, pd.DataFrame({'製番名': [name], '合計時間': [total_time]})], ignore_index=True)

            # Print the resulting DataFrame
            print(result_df)

            #excelに貼り付け♪
            #集計.xlsx
            output_syuukei_path = os.path.join(settings.MEDIA_ROOT,'集計.xlsx')
            final_result.to_excel(output_syuukei_path, index=False)
            #製番.xlsx
            output_seibann_path = os.path.join(settings.MEDIA_ROOT,'製番.xlsx')
            result_df.to_excel(output_seibann_path, index=False)
            success = '集計.xlsxと、製番.xlsxの生成が完了しました'
            return render(request, "syuukei/upload.html", {'success': success})
        except Exception:
            #logger.exception(f"エラーが発生しました： {str(e)}")
            return render(request, 'syuukei/download.html')
    else:
        return render(request, "syuukei/upload.html",)
        

def download_syuukei_file(request):
    output_syuukei_path = os.path.join(settings.MEDIA_ROOT, '集計.xlsx')
    if os.path.exists(output_syuukei_path):
        with open(output_syuukei_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="集計.xlsx"'
        os.remove(output_syuukei_path)
        return response
    else:
        return render(request, "syuukei/download.html")

def download_seibann_file(request):
    output_seibann_path = os.path.join(settings.MEDIA_ROOT, '製番.xlsx')
    if os.path.exists(output_seibann_path):
        with open(output_seibann_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="製番.xlsx"'
        os.remove(output_seibann_path)
        return response
    else:
        return render(request, "syuukei/download.html")
    

