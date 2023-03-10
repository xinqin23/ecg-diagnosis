
import wfdb
import numpy as np
import pandas as pd

from glob import glob
import argparse
import os
from QRSDetectorOffline import QRSDetectorOffline

def check_and_make_dir(folder_name):  # make the repo
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def gen_time_signal(step, n):
    start = 0.0  # the starting value
    time_sig = [start]
    for i in range(1, n):
        t = start + i * step  # calculate the next value
        time_sig.append(t)  # add the value to the list

    return time_sig

def gen_reference_csv(data_dir, reference_csv):
    recordpaths = glob(os.path.join(data_dir, '*.hea'))
    results = []
    no_qrs_detected_num = 0
    for recordpath in recordpaths:
        patient_id = recordpath.split('/')[-1][:-4]
        data, meta_data = wfdb.rdsamp(recordpath[:-4])

        sample_rate = meta_data['fs']
        signal_len = meta_data['sig_len']
        age = meta_data['comments'][0]
        sex = meta_data['comments'][1]
        dx = meta_data['comments'][2]
        age = age[5:] if age.startswith('Age: ') else np.NaN
        sex = sex[5:] if sex.startswith('Sex: ') else 'Unknown'
        dx = dx[4:] if dx.startswith('Dx: ') else ''
        dxs = [dx_dict.get(code, '') for code in dx.split(',')]  # already label RBBB etc

        for label in dxs:
            # store_folder = 'data_se_1as_tstep/{}/'.format(label)
            store_folder = 'qrs_normal_step/{}/'.format(label)
            check_and_make_dir(store_folder)

            # detect qrs here
            qrs_detector = QRSDetectorOffline(data, frequency=500, verbose=False)
            ecgs = qrs_detector.ecg_data_detected   # we cut around the qrs
            rpeaks = qrs_detector.qrs_peaks_indices
            period = qrs_detector.refractory_period
            # data_v6 = ecgs[:, 11][int(rpeaks[0] - period / 2): int( rpeaks[0] + period / 2)]
            # data_v6=  ecgs[:, 11]  #todo: 11 or 10 here????
            # shouldn't here be 10????
            data_v6 = ecgs[:, 10][int(rpeaks[0] - period / 2): int( rpeaks[0] + period / 2)]


            # use raw data
            # data_v6 = data[:,11] # V6

            try:
                file_name = os.path.join(store_folder, '{}.csv'.format(patient_id[5:]))  # remove 'CPSC\\'
                timestamp = gen_time_signal(1/sample_rate, len(data_v6))
                # timestamp = gen_time_signal(1, len(data_v6))

                df = pd.DataFrame({'timestamp': timestamp , 'value': data_v6}) # todo: check sample rate
                df.to_csv(file_name)
            except:
                pass
            else:
                no_qrs_detected_num += 1  # for this si

    print("Number of no QRS Detected: ", no_qrs_detected_num)





if __name__ == "__main__":
    leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    dx_dict = {
        '426783006': 'SNR', # Normal sinus rhythm
        '164889003': 'AF', # Atrial fibrillation
        '270492004': 'IAVB', # First-degree atrioventricular block
        '164909002': 'LBBB', # Left bundle branch block
        '713427006': 'RBBB', # Complete right bundle branch block
        '59118001': 'RBBB', # Right bundle branch block
        '284470004': 'PAC', # Premature atrial contraction
        '63593006': 'PAC', # Supraventricular premature beats
        '164884008': 'PVC', # Ventricular ectopics
        '429622005': 'STD', # ST-segment depression
        '164931005': 'STE', # ST-segment elevation
    }
    classes = ['SNR', 'AF', 'IAVB', 'LBBB', 'RBBB', 'PAC', 'PVC', 'STD', 'STE']
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str, default='data/CPSC/CPSC', help='Directory to dataset')
    args = parser.parse_args()
    data_dir = args.data_dir
    reference_csv = os.path.join(data_dir, 'reference.csv')
    label_csv = os.path.join(data_dir, 'labels.csv')
    gen_reference_csv(data_dir, reference_csv)
    # gen_label_csv(label_csv, reference_csv, dx_dict, classes)
